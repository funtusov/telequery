# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Important**: Always read the README.md file at the start of each session for the latest project information and setup instructions.

## Project Overview

This is the Telequery AI project - a Python-based intelligent query interface for Telegram message history. The system provides semantic search and AI-powered synthesis of answers from a user's Telegram archive.

## Architecture

### Core Components (Planned)
- **Pydantic Agent**: Central orchestrator using strongly-typed models for all data flow
- **FastAPI Service**: RESTful API exposing `/status` and `/query` endpoints
- **Semantic Search Tool**: `search_relevant_messages` function using vector embeddings
- **LLM Integration**: Abstraction layer supporting multiple LLM providers
- **SQLite Database**: Pre-populated with Telegram message data

### Technology Stack
- Python 3.10+
- FastAPI for API framework
- Pydantic for data validation
- SQLite for message storage
- Vector search library (FAISS or ChromaDB)
- LLM abstraction layer (OpenAI, Anthropic, Google, or local models)

## Development Commands

**IMPORTANT: This project uses `uv` as the preferred package manager for faster dependency management.**

**CRITICAL: Always use `uv run python` instead of `python` directly to ensure the correct virtual environment is used.**

```bash
# RECOMMENDED: Start with Docker (uses external ../telequery_db)
./start_docker.sh

# Alternative: Install dependencies using uv for local development
uv pip install -r requirements.txt

# Alternative: Create Python virtual environment (if not using uv)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Alternative: Start the server locally (uses ../telequery_db)
./start_server.sh

# Alternative: Run the FastAPI server manually
uv run uvicorn main:app --reload

# Run full end-to-end test
uv run python run_test.py

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run pylint src/

# Run message expansion script (standalone)
uv run python run_expansion.py

# Run message expansion with custom batch size (default: 50)
uv run python run_expansion.py --batch-size 25

# Show expansion statistics only
uv run python run_expansion.py --stats

# Check Python function signatures and documentation
uv run python -c "import module_name; help(module_name.function_name)"
# Example: uv run python -c "import logfire; help(logfire.configure)"
```

## Database Location

**IMPORTANT**: All database files are stored in `../telequery_db/` (outside the project directory) to:
- Keep databases persistent across deployments
- Allow easy Docker volume mounting
- Separate code from data

The directory structure is:
```
../telequery_db/
├── telegram_messages.db      # Main Telegram messages database
├── telequery_expansions.db   # Message expansion database
└── chroma_db/                # Vector embeddings database
```

## Environment Variables

- `OPENAI_API_KEY`: Required. Your OpenAI API key for LLM operations
- `DATABASE_URL`: SQLite database URL (default: `sqlite:///../telequery_db/telegram_messages.db`)
- `CHROMA_DB_PATH`: ChromaDB vector database path (default: `../telequery_db/chroma_db`)
- `EXPANSION_DB_PATH`: Expansion database path (default: `../telequery_db/telequery_expansions.db`)
- `DISABLE_EXPANSION_ON_STARTUP`: Set to `true` to disable automatic message expansion when server starts (default: `false`)

## Project Structure (Recommended)

```
mindgarden/
├── src/
│   ├── __init__.py
│   ├── agent/           # Pydantic agent implementation
│   ├── api/             # FastAPI endpoints
│   ├── tools/           # Search and other tools
│   ├── models/          # Pydantic models
│   └── llm/             # LLM abstraction layer
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Key Implementation Notes

1. **Message Search**: The `search_relevant_messages` tool must implement semantic search, not just keyword matching. Use vector embeddings to find conceptually related messages.

2. **API Response Format**: All API responses must follow the exact JSON structure defined in the PRD, particularly for the `/query` endpoint.

3. **LLM Integration**: Use an abstraction layer to allow switching between different LLM providers without changing core logic.

4. **Error Handling**: The agent should clearly state when it cannot find an answer rather than hallucinating responses.

5. **Database Schema**: Ensure the SQLite schema supports efficient querying by chat_id, user_id, and timestamp ranges.

6. **Message Expansion**: The system uses batch processing with JSON structured responses to efficiently expand messages with context. Batches of 50 messages are processed with 10-message overlaps for context continuity.

7. **Python Commands**: Always use `uv run python` instead of `python` directly to ensure the correct virtual environment is used.

8. **Function Signatures**: When implementing integrations with Python libraries, always check function signatures using Python's help() function:
   ```bash
   uv run python -c "import library_name; help(library_name.function_name)"
   ```
   This ensures correct parameter names and types are used.

## Testing Strategy

- Unit tests for each tool function
- Integration tests for the full agent pipeline
- API endpoint tests using FastAPI's test client
- Mock LLM responses for predictable testing

**IMPORTANT Testing Best Practice:**
- **ALWAYS run tests incrementally after creating each test file**
- **DO NOT create all test files at once without running them**
- **Fix any issues immediately before proceeding to the next test**
- This ensures tests actually work with the current implementation
- Use `uv run pytest tests/ -v` to run all tests
- Use `uv run pytest tests/test_specific.py -v` to run specific test file

## Git Commit Guidelines

**EXTREMELY IMPORTANT - CRITICAL REQUIREMENT:**
- **ALWAYS USE ONE-LINE COMMIT MESSAGES - NO MULTI-LINE COMMITS**
- **NEVER USE MULTI-LINE COMMIT MESSAGES WITH DESCRIPTIONS OR BULLET POINTS**
- **ONE LINE ONLY - NO EXCEPTIONS**
- Do not mention Claude Code or AI assistance in commit messages
- Focus on what changed, not who or what made the change
- Example: `git commit -m "Add FastAPI server with status endpoint"`
- NOT: `git commit -m "Add FastAPI server\n\n- Created main.py\n- Added status endpoint"`