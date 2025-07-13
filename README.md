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

## Architecture

The system consists of:
- A Pydantic-based agent that orchestrates the query process
- FastAPI service exposing query endpoints
- Semantic search using vector embeddings
- SQLite database containing pre-indexed Telegram messages
- LLM integration for answer synthesis

## Prerequisites

- Python 3.10 or higher
- SQLite database populated with Telegram messages (see Database Setup section)
- API key for your chosen LLM provider

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/telequery-ai.git
cd telequery-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
# LLM Configuration
LLM_PROVIDER=openai  # Options: openai, anthropic, google, local
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4  # Or your preferred model

# Database
DATABASE_PATH=./data/telegram_messages.db

# Vector Search
VECTOR_INDEX_PATH=./data/message_embeddings.index
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

### Starting the API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
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
pytest tests/
```

### Code Formatting
```bash
black .
```

### Linting
```bash
pylint src/
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