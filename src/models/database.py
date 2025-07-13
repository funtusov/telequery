from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelegramMessage(BaseModel):
    message_id: str = Field(..., description="Unique message identifier")
    chat_id: str = Field(..., description="Chat/group ID where message was sent")
    user_id: str = Field(..., description="User ID who sent the message")
    sender_name: str = Field(..., description="Display name of the sender")
    text: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="When the message was sent")
    reply_to_message_id: Optional[str] = Field(None, description="ID of message being replied to")
    
    class Config:
        orm_mode = True