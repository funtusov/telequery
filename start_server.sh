#!/bin/bash

# Telequery AI Server Startup Script
# This script loads environment variables and starts the FastAPI server
# using the database in the tmp/ directory

set -e  # Exit on any error

echo "🚀 Starting Telequery AI Server"
echo "================================"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first."
    exit 1
fi

echo "📦 Using uv for dependency management..."

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    set -a  # automatically export all variables
    source .env
    set +a  # stop automatically exporting
else
    echo "⚠️  No .env file found. Make sure OPENAI_API_KEY is set."
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable is not set!"
    echo "Please create a .env file with your OpenAI API key:"
    echo "OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

echo "✅ OpenAI API key found: ${OPENAI_API_KEY:0:8}..."

# Set database URL to use external telequery_db directory
export DATABASE_URL="sqlite:///../telequery_db/telegram_messages.db"
export CHROMA_DB_PATH="../telequery_db/chroma_db"
export EXPANSION_DB_PATH="../telequery_db/telequery_expansions.db"

echo "📊 Database: $DATABASE_URL"
echo "🔍 ChromaDB: $CHROMA_DB_PATH"
echo "📈 Expansion DB: $EXPANSION_DB_PATH"

# Check if database exists in ../telequery_db/
if [ ! -f "../telequery_db/telegram_messages.db" ]; then
    echo "❌ Database not found in ../telequery_db/telegram_messages.db"
    echo "Please run the test script first to create sample data:"
    echo "python run_test.py"
    exit 1
fi

echo "✅ Database found in ../telequery_db/"

# Check if ChromaDB data exists
if [ ! -d "../telequery_db/chroma_db" ]; then
    echo "⚠️  ChromaDB not found in ../telequery_db/. Server will create it on first query."
    mkdir -p ../telequery_db/chroma_db
fi

# Start the FastAPI server
echo ""
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/status"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

# Start the server with uv run python -m uvicorn
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload