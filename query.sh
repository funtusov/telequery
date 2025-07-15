#!/bin/bash

# Telequery AI Query Script
# This script sends a query to the Telequery AI server

# Default values
SERVER_URL="${TELEQUERY_SERVER_URL:-http://localhost:8000}"
USER_ID="${TELEGRAM_USER_ID:-default_user}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"
DEBUG_MODE=false

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS] \"Your question here\""
    echo ""
    echo "Options:"
    echo "  -u, --user-id USER_ID    Telegram user ID (default: $USER_ID)"
    echo "  -c, --chat-id CHAT_ID    Telegram chat ID (optional)"
    echo "  -s, --server URL         Server URL (default: $SERVER_URL)"
    echo "  -d, --debug              Enable debug mode (show expanded messages and scores)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 \"What did we discuss about the project?\""
    echo "  $0 -u john_doe \"Tell me about our meeting yesterday\""
    echo "  $0 -u alice -c general_chat \"What are the latest updates?\""
    echo ""
    echo "Environment variables:"
    echo "  TELEQUERY_SERVER_URL     Override default server URL"
    echo "  TELEGRAM_USER_ID         Override default user ID"
    echo "  TELEGRAM_CHAT_ID         Override default chat ID"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user-id)
            USER_ID="$2"
            shift 2
            ;;
        -c|--chat-id)
            CHAT_ID="$2"
            shift 2
            ;;
        -s|--server)
            SERVER_URL="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done

# Check if query is provided
if [ -z "$QUERY" ]; then
    echo -e "${RED}Error: No query provided${NC}"
    usage
    exit 1
fi

# Check if server is running
if ! curl -s "${SERVER_URL}/status" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to server at ${SERVER_URL}${NC}"
    echo "Make sure the server is running with: ./start_server.sh"
    exit 1
fi

echo -e "${YELLOW}Sending query to Telequery AI...${NC}"
echo -e "Server: ${SERVER_URL}"
echo -e "User: ${USER_ID}"
if [ -n "$CHAT_ID" ]; then
    echo -e "Chat: ${CHAT_ID}"
fi
if [ "$DEBUG_MODE" = true ]; then
    echo -e "Mode: DEBUG"
fi
echo -e "Query: \"${QUERY}\""
echo ""

# Build JSON payload
if [ -n "$CHAT_ID" ]; then
    JSON_PAYLOAD=$(cat <<EOF
{
    "user_question": "${QUERY}",
    "telegram_user_id": "${USER_ID}",
    "telegram_chat_id": "${CHAT_ID}",
    "debug": ${DEBUG_MODE}
}
EOF
)
else
    JSON_PAYLOAD=$(cat <<EOF
{
    "user_question": "${QUERY}",
    "telegram_user_id": "${USER_ID}",
    "debug": ${DEBUG_MODE}
}
EOF
)
fi

# Send the request
RESPONSE=$(curl -s -X POST "${SERVER_URL}/query" \
    -H "Content-Type: application/json" \
    -d "${JSON_PAYLOAD}" 2>&1)

# Check if curl succeeded
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to send request${NC}"
    echo "$RESPONSE"
    exit 1
fi

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo -e "${RED}Error: Invalid response from server${NC}"
    echo "$RESPONSE"
    exit 1
fi

# Extract and display the answer
STATUS=$(echo "$RESPONSE" | jq -r '.status // "error"')

if [ "$STATUS" = "success" ]; then
    # Show rewritten query in debug mode
    if [ "$DEBUG_MODE" = true ]; then
        REWRITTEN_QUERY=$(echo "$RESPONSE" | jq -r '.rewritten_query // empty')
        if [ -n "$REWRITTEN_QUERY" ]; then
            echo -e "${YELLOW}🔄 Rewritten Query: ${REWRITTEN_QUERY}${NC}"
            echo ""
        fi
    fi
    
    echo -e "${GREEN}Answer:${NC}"
    echo "$RESPONSE" | jq -r '.answer_text'
    
    # Show source messages if available
    SOURCE_COUNT=$(echo "$RESPONSE" | jq '.source_messages | length')
    if [ "$SOURCE_COUNT" -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Based on ${SOURCE_COUNT} source message(s):${NC}"
        
        if [ "$DEBUG_MODE" = true ]; then
            # Debug mode: show all messages with expanded text and scores
            echo "$RESPONSE" | jq -r '.source_messages[] | 
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
                "📊 Relevance Score: \(.relevance_score // "N/A")\n" +
                "👤 Sender: \(.sender)\n" +
                "🕐 Time: \(.timestamp)\n" +
                "📝 Original: \(.text)\n" +
                if .expanded_text then
                    "🔍 Expanded:\n\(.expanded_text)\n"
                else
                    ""
                end'
        else
            # Normal mode: show truncated list
            echo "$RESPONSE" | jq -r '.source_messages[] | "- [\(.timestamp)] \(.sender): \(.text)"' | head -10
            
            if [ "$SOURCE_COUNT" -gt 10 ]; then
                echo "... and $((SOURCE_COUNT - 10)) more messages"
            fi
        fi
    fi
else
    echo -e "${RED}Error: Query failed${NC}"
    echo "$RESPONSE" | jq -r '.detail // .message // .'
    exit 1
fi