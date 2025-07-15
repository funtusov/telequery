from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import signal
import sys

from ..models.api import HealthCheckResponse, QueryRequest, QueryResponse
from ..models.agent import AgentContext
from ..agent.telequery_agent import TelequeryAgent
from ..services.expansion_service import startup_expansion_check
import os

app = FastAPI(
    title="Telequery AI",
    description="Intelligent query interface for Telegram message history",
    version="1.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track background tasks
background_tasks = set()
shutdown_event = asyncio.Event()


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Shutdown signal received. Stopping background tasks...")
    shutdown_event.set()
    # Cancel all background tasks
    for task in background_tasks:
        task.cancel()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


@app.on_event("startup")
async def startup_event():
    """Run startup tasks including expansion service check."""
    # Check if expansion should be disabled
    if os.getenv("DISABLE_EXPANSION_ON_STARTUP", "false").lower() == "true":
        print("📌 Expansion on startup is disabled (DISABLE_EXPANSION_ON_STARTUP=true)")
        return
    
    # Run expansion check in background task
    task = asyncio.create_task(run_expansion_in_background())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


async def run_expansion_in_background():
    """Run expansion service in background without blocking startup."""
    try:
        await startup_expansion_check()
    except asyncio.CancelledError:
        print("🛑 Expansion service cancelled")
        raise
    except Exception as e:
        print(f"❌ Background expansion error: {e}")


@app.get("/status", response_model=HealthCheckResponse)
async def health_check():
    """Check if the service is running and healthy."""
    return HealthCheckResponse(status="ok", version="1.1")


@app.post("/query", response_model=QueryResponse)
async def query_messages(request: QueryRequest):
    """Process a user question and return an AI-generated answer."""
    try:
        # Get database configuration
        database_url = os.getenv("DATABASE_URL", "sqlite:///./telegram_messages.db")
        chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
        expansion_db_path = os.getenv("EXPANSION_DB_PATH", "./data/telequery_expansions.db")
        
        # Create agent with database configuration
        agent = TelequeryAgent(
            database_url=database_url,
            chroma_path=chroma_path,
            expansion_db_path=expansion_db_path
        )
        
        # Create agent context from request
        context = AgentContext(
            user_question=request.user_question,
            telegram_user_id=request.telegram_user_id,
            telegram_chat_id=request.telegram_chat_id,
            debug=request.debug
        )
        
        # Process the query using the agent
        response = await agent.process_query(context)
        return response
        
    except Exception as e:
        print(f"Query endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return QueryResponse(
            answer_text=f"An error occurred: {str(e)}",
            source_messages=[],
            status="error"
        )