# Telequery AI

An intelligent query interface for Telegram message history that transforms your chat archive into a searchable knowledge base.

## Overview

Telequery AI enables users to ask natural language questions about their Telegram message history and receive synthesized, context-aware answers. Instead of manually searching through thousands of messages, users can simply ask questions like "Who is responsible for electricity at the camp?" and get accurate answers with source citations.

## Features

- **Semantic Search**: Find conceptually related messages, not just keyword matches
- **AI-Powered Synthesis**: Get concise, contextual answers from your message history
- **Source Citations**: Every answer includes references to the original messages
- **RESTful API**: Easy integration with Telegram bots or other applications
- **Flexible LLM Support**: Works with OpenAI, Anthropic, Google, or local models
- **Docker Ready**: Containerized for easy deployment and development

## Architecture

The system consists of:
- A Pydantic-based agent that orchestrates the query process
- FastAPI service exposing query endpoints
- Semantic search using vector embeddings
- SQLite database containing pre-indexed Telegram messages
- LLM integration for answer synthesis

## Prerequisites

- Docker and Docker Compose
- SQLite database populated with Telegram messages (see Database Setup section)
- API key for your chosen LLM provider (OpenAI recommended)

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/telequery-ai.git
   cd telequery-ai
   ```

2. **Set up environment variables**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   ```

3. **Start the application**
   ```bash
   ./start_docker.sh
   ```

The application will be available at `http://localhost:8000`

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: **Required**. Your OpenAI API key for LLM operations
- `DATABASE_URL`: SQLite database URL (default: `sqlite:///../telequery_db/telegram_messages.db`)
- `CHROMA_DB_PATH`: ChromaDB vector database path (default: `../telequery_db/chroma_db`)
- `EXPANSION_DB_PATH`: Expansion database path (default: `../telequery_db/telequery_expansions.db`)
- `DISABLE_EXPANSION_ON_STARTUP`: Set to `true` to disable automatic message expansion when server starts (default: `false`)

### Database Location

All database files are stored in `../telequery_db/` (outside the project directory) to:
- Keep databases persistent across deployments
- Allow easy Docker volume mounting
- Separate code from data

Directory structure:
```
../telequery_db/
├── telegram_messages.db      # Main Telegram messages database
├── telequery_expansions.db   # Message expansion database
└── chroma_db/                # Vector embeddings database
```

## Database Setup

The SQLite database should have the following schema:

```sql
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    sender_name TEXT,
    timestamp DATETIME NOT NULL,
    text TEXT,
    reply_to_message_id TEXT
);

CREATE INDEX idx_chat_id ON messages(chat_id);
CREATE INDEX idx_user_id ON messages(user_id);
CREATE INDEX idx_timestamp ON messages(timestamp);
```

## Usage

### Docker (Recommended)

```bash
# Start with Docker (rebuilds image and starts container)
./start_docker.sh

# Query the API using the client script
./query.sh "Who is responsible for electricity at the camp?"

# Or with explicit parameters
./query.sh -u john_doe -c general_chat "What did we discuss about the project?"
```

### Local Development (Alternative)

For local development without Docker:

```bash
# Install dependencies with uv (recommended)
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt

# Start the server manually
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Health Check
```bash
GET /status
```

Response:
```json
{
  "status": "ok",
  "version": "1.1"
}
```

#### Query Messages
```bash
POST /query
```

Request body:
```json
{
  "user_question": "who takes care of electricity for the camp?",
  "telegram_user_id": "user12345",
  "telegram_chat_id": "group-98765"
}
```

Response:
```json
{
  "answer_text": "It appears that Alice (@alice_tg) is responsible for the electricity. She mentioned on June 28th that she would be bringing the main generator and coordinating the power grid.",
  "source_messages": [
    {
      "message_id": "msg_abcde",
      "sender": "Alice",
      "timestamp": "2025-06-28T14:30:00Z",
      "text": "Hey everyone, just confirming I've got the main generator covered for our camp's electricity. I'll map out the power grid plan this weekend."
    }
  ],
  "status": "success"
}
```

## Development

### Running Tests
```bash
# With uv (recommended)
uv run pytest tests/

# Or with pip
pytest tests/
```

### Code Formatting
```bash
# With uv (recommended)
uv run black .

# Or with pip
black .
```

### Linting
```bash
# With uv (recommended)
uv run pylint src/

# Or with pip
pylint src/
```

### Additional Commands

```bash
# Run full end-to-end test
uv run python run_test.py

# Run message expansion script
uv run python run_expansion.py

# Run message expansion with custom batch size
uv run python run_expansion.py --batch-size 25

# Show expansion statistics only
uv run python run_expansion.py --stats
```

## Project Structure

```
telequery-ai/
├── src/
│   ├── agent/           # Pydantic agent implementation
│   ├── api/             # FastAPI endpoints
│   ├── tools/           # Search and other tools
│   ├── models/          # Pydantic models
│   └── llm/             # LLM abstraction layer
├── tests/               # Test suite
├── data/                # Database and index files
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## License

[Your chosen license]

## Contributing

[Contribution guidelines]

## Support

[Support information]