#!/bin/bash

# Telequery AI Server Startup Script
# This script loads environment variables and starts the FastAPI server
# using the database in the tmp/ directory

set -e  # Exit on any error

echo "🚀 Starting Telequery AI Server"
echo "================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv venv' first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

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

# Set database URL to use tmp directory
export DATABASE_URL="sqlite:///./tmp/telegram_messages.db"
export CHROMA_DB_PATH="./tmp/chroma_db"

echo "📊 Database: $DATABASE_URL"
echo "🔍 ChromaDB: $CHROMA_DB_PATH"

# Check if database exists in tmp/
if [ ! -f "tmp/telegram_messages.db" ]; then
    echo "❌ Database not found in tmp/telegram_messages.db"
    echo "Please run the test script first to create sample data:"
    echo "python run_test.py"
    exit 1
fi

echo "✅ Database found in tmp/"

# Check if ChromaDB data exists
if [ ! -d "tmp/chroma_db" ]; then
    echo "⚠️  ChromaDB not found in tmp/. Server will create it on first query."
    mkdir -p tmp/chroma_db
fi

# Start the FastAPI server
echo ""
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/status"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

# Start the server with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload