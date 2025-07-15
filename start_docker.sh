#!/bin/bash

# Defaults
IMAGE_NAME="telequery-ai"
CONTAINER_NAME="telequery-ai-container"
HOST_PORT=8000
CONTAINER_PORT=8000
MAIN_DB_HOST_PATH="$(pwd)/../telequery_db/telegram_messages.db"
EXPANSION_DB_HOST_PATH="$(pwd)/../telequery_db/telequery_expansions.db"
VECTOR_HOST_PATH="$(pwd)/../telequery_db"
ENV_FILE=".env"

# Parse arguments (e.g., --main-db /path/to/main.db --expansion-db /path/to/exp.db)
while [[ $# -gt 0 ]]; do
    case $1 in
        --main-db) MAIN_DB_HOST_PATH="$2"; shift 2 ;;
        --expansion-db) EXPANSION_DB_HOST_PATH="$2"; shift 2 ;;
        --env-file) ENV_FILE="$2"; shift 2 ;;
        --host-port) HOST_PORT="$2"; shift 2 ;;
        *) echo "Unknown option $1"; exit 1 ;;
    esac
done

# Log database file paths
echo "Database configuration:"
echo "  Main database: $MAIN_DB_HOST_PATH"
echo "  Expansion database: $EXPANSION_DB_HOST_PATH"
echo "  Vector database directory: $VECTOR_HOST_PATH/chroma_db"

# Check if database files exist
if [ -f "$MAIN_DB_HOST_PATH" ]; then
    echo "  ✓ Main database file exists"
else
    echo "  ⚠ Main database file not found (will be created on first run)"
fi

if [ -f "$EXPANSION_DB_HOST_PATH" ]; then
    echo "  ✓ Expansion database file exists"
else
    echo "  ⚠ Expansion database file not found (will be created on first run)"
fi

if [ -d "$VECTOR_HOST_PATH/chroma_db" ]; then
    echo "  ✓ Vector database directory exists"
else
    echo "  ⚠ Vector database directory not found (will be created on first run)"
fi

echo ""

# Always rebuild the image to ensure changes are applied
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Stop and remove existing container if running
docker stop $CONTAINER_NAME > /dev/null 2>&1
docker rm $CONTAINER_NAME > /dev/null 2>&1

# Run container
echo "Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $HOST_PORT:$CONTAINER_PORT \
    -v $MAIN_DB_HOST_PATH:/app/data/telequery_db/telegram_messages.db \
    -v $EXPANSION_DB_HOST_PATH:/app/data/telequery_db/telequery_expansions.db \
    -v $VECTOR_HOST_PATH/chroma_db:/app/data/chroma_db \
    -e MAIN_DB_PATH=/app/data/telequery_db/telegram_messages.db \
    -e EXPANSION_DB_PATH=/app/data/telequery_db/telequery_expansions.db \
    --env-file $ENV_FILE \
    $IMAGE_NAME

echo "Telequery AI running at http://localhost:$HOST_PORT"
echo "Logs: docker logs -f $CONTAINER_NAME"