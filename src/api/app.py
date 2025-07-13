from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..models.api import HealthCheckResponse, QueryRequest, QueryResponse

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
    # TODO: Implement the full agent flow
    return QueryResponse(
        answer_text="Query endpoint not yet implemented",
        source_messages=[],
        status="not_implemented"
    )