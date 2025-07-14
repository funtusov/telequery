import os
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, create_engine, text
from sqlalchemy.orm import sessionmaker

import chromadb
from chromadb.utils import embedding_functions

from ..models.agent import SearchToolInput, SearchToolOutput
from ..models.database import TelegramMessage


class MessageSearchTool:
    def __init__(self, chroma_path: str = "./chroma_db", database_url: str = "sqlite:///./telegram_messages.db"):
        self.chroma_path = chroma_path
        self.database_url = database_url
        
        # Setup database connection
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Setup ChromaDB
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        # Use OpenAI embeddings
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
    
    def populate_search_index(self):
        """Populate the search index with all messages from the database."""
        print("🔍 Populating search index from database...")
        
        with self.SessionLocal() as session:
            # Get all messages with chat info
            query = text("""
                SELECT m.telegram_id, m.text, m.sender_name, m.telegram_date, c.telegram_id as chat_telegram_id
                FROM messages m
                JOIN chats c ON m.chat_id = c.id
                WHERE m.text IS NOT NULL AND m.text != ''
            """)
            
            results = session.execute(query).fetchall()
            
            if not results:
                print("⚠️  No messages found in database")
                return
            
            # Clear existing collection
            try:
                self.client.delete_collection("telegram_messages")
                openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model_name="text-embedding-3-small"
                )
                self.collection = self.client.get_or_create_collection(
                    name="telegram_messages",
                    embedding_function=openai_ef
                )
            except:
                pass
            
            # Add messages to search index
            documents = []
            metadatas = []
            ids = []
            
            for row in results:
                telegram_id, message_text, sender_name, telegram_date, chat_telegram_id = row
                
                # Create searchable text
                searchable_text = f"{message_text}\nSender: {sender_name}\nTime: {telegram_date}"
                
                documents.append(searchable_text)
                metadatas.append({
                    "telegram_id": str(telegram_id),
                    "chat_telegram_id": str(chat_telegram_id),
                    "sender_name": sender_name or "Unknown",
                    "telegram_date": str(telegram_date)
                })
                ids.append(f"msg_{telegram_id}")
            
            # Batch add to collection
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Added {len(documents)} messages to search index")
    
    def search_relevant_messages(self, search_input: SearchToolInput) -> SearchToolOutput:
        """Search for messages using semantic search."""
        # Build metadata filters
        where_clause = {}
        if search_input.chat_id:
            where_clause["chat_telegram_id"] = search_input.chat_id
        
        # Perform semantic search
        try:
            results = self.collection.query(
                query_texts=[search_input.query_text],
                n_results=10,
                where=where_clause if where_clause else None
            )
        except Exception as e:
            print(f"Search error: {e}")
            return SearchToolOutput(messages=[], total_found=0)
        
        if not results["ids"] or not results["ids"][0]:
            return SearchToolOutput(messages=[], total_found=0)
        
        # Extract telegram_ids from the results
        telegram_ids = []
        for metadata in results["metadatas"][0]:
            telegram_ids.append(int(metadata["telegram_id"]))
        
        # Get full message details from database
        with self.SessionLocal() as session:
            placeholders = ','.join(str(tid) for tid in telegram_ids)
            query = text(f"""
                SELECT m.telegram_id, m.text, m.sender_name, m.telegram_date, 
                       c.telegram_id as chat_telegram_id, m.reply_to_message_id
                FROM messages m
                JOIN chats c ON m.chat_id = c.id
                WHERE m.telegram_id IN ({placeholders})
            """)
            
            db_messages = session.execute(query).fetchall()
        
        # Convert to TelegramMessage objects and maintain search result order
        telegram_messages = []
        for telegram_id in telegram_ids:
            for row in db_messages:
                if row[0] == telegram_id:  # telegram_id matches
                    # Parse timestamp if it's a string
                    timestamp = row[3]
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    telegram_messages.append(TelegramMessage(
                        message_id=str(row[0]),  # Convert telegram_id to string
                        chat_id=str(row[4]),     # chat_telegram_id
                        user_id="unknown",       # Not available in this schema
                        sender_name=row[2] or "Unknown",
                        text=row[1] or "",
                        timestamp=timestamp,
                        reply_to_message_id=str(row[5]) if row[5] else None
                    ))
                    break
        
        return SearchToolOutput(
            messages=telegram_messages,
            total_found=len(telegram_messages)
        )


# Global instance - will be initialized when needed
search_tool = None

def get_search_tool(database_url: str = "sqlite:///./telegram_messages.db", chroma_path: str = "./chroma_db"):
    """Get or create the search tool instance."""
    global search_tool
    if search_tool is None:
        search_tool = MessageSearchTool(chroma_path=chroma_path, database_url=database_url)
        # Populate search index on first use
        search_tool.populate_search_index()
    return search_tool