from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", description="Service status")
    version: str = Field(default="1.1", description="API version")


class QueryRequest(BaseModel):
    user_question: str = Field(..., description="The user's question to be answered")
    telegram_user_id: str = Field(..., description="Telegram user ID making the request")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID to search within")
    debug: bool = Field(False, description="Enable debug mode to show expanded messages and scores")


class SourceMessage(BaseModel):
    message_id: str = Field(..., description="Unique message identifier")
    sender: str = Field(..., description="Name of the message sender")
    timestamp: datetime = Field(..., description="When the message was sent")
    text: str = Field(..., description="Content of the message")
    expanded_text: Optional[str] = Field(None, description="LLM-expanded version of the message")
    relevance_score: Optional[float] = Field(None, description="Semantic similarity score")


class QueryResponse(BaseModel):
    answer_text: str = Field(..., description="AI-generated answer to the question")
    source_messages: List[SourceMessage] = Field(default_factory=list, description="Messages used to generate the answer")
    status: str = Field(default="success", description="Query execution status")
    rewritten_query: Optional[str] = Field(None, description="LLM-rewritten version of the original query")