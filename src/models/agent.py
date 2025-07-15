from datetime import datetime
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

from .database import TelegramMessage


class SearchToolInput(BaseModel):
    query_text: str = Field(..., description="The search query")
    chat_id: Optional[str] = Field(None, description="Specific chat to search within")
    time_range: Optional[Tuple[datetime, datetime]] = Field(None, description="Time range filter")
    user_id: Optional[str] = Field(None, description="Filter by specific user")
    debug: bool = Field(False, description="Return debug information including scores")


class MessageWithScore(BaseModel):
    message: TelegramMessage
    relevance_score: float = Field(..., description="Semantic similarity score")
    expanded_text: Optional[str] = Field(None, description="LLM-expanded version if available")


class SearchToolOutput(BaseModel):
    messages: List[TelegramMessage] = Field(default_factory=list, description="Relevant messages found")
    total_found: int = Field(0, description="Total number of matching messages")
    messages_with_scores: Optional[List[MessageWithScore]] = Field(None, description="Messages with debug info")
    rewritten_query: Optional[str] = Field(None, description="LLM-rewritten version of the query")


class AgentContext(BaseModel):
    user_question: str = Field(..., description="Original user question")
    telegram_user_id: str = Field(..., description="User making the request")
    telegram_chat_id: Optional[str] = Field(None, description="Chat context")
    debug: bool = Field(False, description="Enable debug mode")


class LLMPrompt(BaseModel):
    system_prompt: str = Field(..., description="System instructions for the LLM")
    user_prompt: str = Field(..., description="User query with context")
    context_messages: List[TelegramMessage] = Field(default_factory=list, description="Messages to use as context")