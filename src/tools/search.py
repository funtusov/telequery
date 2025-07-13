import os
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

import chromadb
from chromadb.utils import embedding_functions

from ..models.agent import SearchToolInput, SearchToolOutput
from ..models.database import TelegramMessage
from ..models.schema import Message
from ..database.connection import SessionLocal


class MessageSearchTool:
    def __init__(self, chroma_path: str = "./chroma_db"):
        self.chroma_path = chroma_path
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        # Use OpenAI embeddings (can be configured later)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for embeddings")
            
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small"
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="telegram_messages",
            embedding_function=openai_ef
        )
    
    def add_message_to_index(self, message: TelegramMessage):
        """Add a message to the vector index."""
        # Create a searchable text combining message content with metadata
        searchable_text = f"{message.text}\nSender: {message.sender_name}\nTime: {message.timestamp}"
        
        self.collection.add(
            documents=[searchable_text],
            metadatas=[{
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "user_id": message.user_id,
                "sender_name": message.sender_name,
                "timestamp": message.timestamp.isoformat()
            }],
            ids=[message.message_id]
        )
    
    def search_relevant_messages(self, search_input: SearchToolInput) -> SearchToolOutput:
        """Search for messages relevant to the query using semantic search."""
        # Build metadata filters
        where_clause = {}
        if search_input.chat_id:
            where_clause["chat_id"] = search_input.chat_id
        if search_input.user_id:
            where_clause["user_id"] = search_input.user_id
        
        # Perform semantic search
        results = self.collection.query(
            query_texts=[search_input.query_text],
            n_results=10,  # Get top 10 most relevant messages
            where=where_clause if where_clause else None
        )
        
        if not results["ids"] or not results["ids"][0]:
            return SearchToolOutput(messages=[], total_found=0)
        
        # Get full message details from database
        message_ids = results["ids"][0]
        
        with SessionLocal() as db:
            query = db.query(Message).filter(Message.message_id.in_(message_ids))
            
            # Apply time range filter if provided
            if search_input.time_range:
                start_time, end_time = search_input.time_range
                query = query.filter(
                    and_(
                        Message.timestamp >= start_time,
                        Message.timestamp <= end_time
                    )
                )
            
            db_messages = query.all()
        
        # Convert to Pydantic models and maintain search result order
        telegram_messages = []
        for message_id in message_ids:
            for db_msg in db_messages:
                if db_msg.message_id == message_id:
                    telegram_messages.append(TelegramMessage(
                        message_id=db_msg.message_id,
                        chat_id=db_msg.chat_id,
                        user_id=db_msg.user_id,
                        sender_name=db_msg.sender_name,
                        text=db_msg.text,
                        timestamp=db_msg.timestamp,
                        reply_to_message_id=db_msg.reply_to_message_id
                    ))
                    break
        
        return SearchToolOutput(
            messages=telegram_messages,
            total_found=len(telegram_messages)
        )


# Global instance - will be initialized when needed
search_tool = None

def get_search_tool():
    """Get or create the search tool instance."""
    global search_tool
    if search_tool is None:
        search_tool = MessageSearchTool()
    return search_tool