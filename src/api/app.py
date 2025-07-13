from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..models.api import HealthCheckResponse, QueryRequest, QueryResponse
from ..models.agent import AgentContext
from ..agent.telequery_agent import TelequeryAgent

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


@app.get("/status", response_model=HealthCheckResponse)
async def health_check():
    """Check if the service is running and healthy."""
    return HealthCheckResponse(status="ok", version="1.1")


@app.post("/query", response_model=QueryResponse)
async def query_messages(request: QueryRequest):
    """Process a user question and return an AI-generated answer."""
    # Initialize the agent
    agent = TelequeryAgent()
    
    # Create agent context from request
    context = AgentContext(
        user_question=request.user_question,
        telegram_user_id=request.telegram_user_id,
        telegram_chat_id=request.telegram_chat_id
    )
    
    # Process the query using the agent
    response = await agent.process_query(context)
    return response