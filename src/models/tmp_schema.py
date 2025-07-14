"""
Adapter models for the existing tmp/ database schema.
This allows us to work with the existing database structure.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TmpTelegramMessage(BaseModel):
    """Message model that matches the tmp/ database schema."""
    telegram_id: int = Field(..., description="Telegram message ID")
    chat_id: int = Field(..., description="Database chat ID (not Telegram chat ID)")
    text: Optional[str] = Field(None, description="Message content")
    message_type: str = Field(default="text", description="Type of message")
    sender_id: Optional[int] = Field(None, description="Telegram sender ID")
    sender_name: Optional[str] = Field(None, description="Display name of sender")
    sender_username: Optional[str] = Field(None, description="Username of sender")
    telegram_date: datetime = Field(..., description="When message was sent")
    is_outgoing: Optional[bool] = Field(False, description="If message is outgoing")
    is_reply: Optional[bool] = Field(False, description="If message is a reply")
    reply_to_message_id: Optional[int] = Field(None, description="ID of replied message")
    
    class Config:
        from_attributes = True


class TmpChat(BaseModel):
    """Chat model that matches the tmp/ database schema."""
    telegram_id: int = Field(..., description="Telegram chat ID")
    name: str = Field(..., description="Chat name")
    username: Optional[str] = Field(None, description="Chat username")
    chat_type: str = Field(..., description="Type of chat")
    is_verified: Optional[bool] = Field(False, description="If chat is verified")
    is_scam: Optional[bool] = Field(False, description="If chat is marked as scam")
    is_fake: Optional[bool] = Field(False, description="If chat is marked as fake")
    
    class Config:
        from_attributes = True