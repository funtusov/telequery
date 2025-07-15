import os
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logfire

import chromadb
from chromadb.utils import embedding_functions

from ..models.agent import SearchToolInput, SearchToolOutput
from ..models.database import TelegramMessage
from ..models.schema import Message as SourceMessage
from ..database.expansion_schema import MessageExpansion
from ..llm.factory import LLMFactory
from ..observability.logfire_config import log_tool_operation

# Load environment variables
load_dotenv()


class MessageSearchTool:
    def __init__(self, chroma_path: str = None, database_url: str = None, expansion_db_url: str = None):
        # Set defaults using environment variables
        self.chroma_path = chroma_path or os.getenv("CHROMA_DB_PATH", "../telequery_db/chroma_db")
        
        # Handle database URL with support for MAIN_DB_PATH
        if database_url:
            self.database_url = database_url
        else:
            main_db_path = os.getenv("MAIN_DB_PATH")
            if main_db_path:
                self.database_url = f"sqlite:///{main_db_path}"
            else:
                self.database_url = os.getenv("DATABASE_URL", "sqlite:///../telequery_db/telegram_messages.db")
        
        self.expansion_db_url = expansion_db_url or os.getenv("EXPANSION_DB_PATH", "../telequery_db/telequery_expansions.db")
        # Convert expansion path to full SQLite URL if needed
        if not self.expansion_db_url.startswith("sqlite:///"):
            self.expansion_db_url = f"sqlite:///{self.expansion_db_url}"
        
        # Setup database connection
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Setup expansion database connection
        self.expansion_engine = create_engine(self.expansion_db_url)
        self.ExpansionSessionLocal = sessionmaker(bind=self.expansion_engine)
        
        # Setup ChromaDB
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        
        # Use OpenAI embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for embeddings")
            
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small"
        )
        
        # Get or create collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name="telegram_messages",
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"}
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
    
    def _get_searchable_text(self, message: SourceMessage, expansion_session: Session) -> str:
        """
        Fetches the expanded text if it exists; otherwise, returns the original text.
        This is a helper to be used within populate_search_index.
        """
        expansion = expansion_session.query(MessageExpansion).filter(
            MessageExpansion.message_id == str(message.telegram_id)
        ).first()
        if expansion and expansion.expanded_text:
            return expansion.expanded_text
        return message.text or ""
    
    def populate_search_index(self):
        """Populate the search index with all messages from the database."""
        print("🔍 Populating search index from database...")
        
        source_session = self.SessionLocal()
        expansion_session = self.ExpansionSessionLocal()
        
        try:
            # Get all messages from the source database using raw SQL
            results = source_session.execute(
                text("SELECT * FROM messages WHERE text IS NOT NULL AND text != ''")
            ).fetchall()
            
            # Convert raw results to message objects
            all_source_messages = []
            for row in results:
                msg = type('Message', (), {
                    'id': row[0],
                    'telegram_id': row[1],
                    'chat_id': row[2],
                    'text': row[3],
                    'message_type': row[4],
                    'sender_id': row[5],
                    'sender_name': row[6],
                    'sender_username': row[7],
                    'telegram_date': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'is_outgoing': row[11],
                    'is_reply': row[12],
                    'reply_to_message_id': row[13],
                    'forward_from_id': row[14],
                    'forward_from_name': row[15],
                    'media_type': row[16],
                    'media_file_id': row[17],
                    'media_file_name': row[18],
                    'media_file_size': row[19],
                    # Add properties for compatibility
                    'message_id': str(row[1]),  # telegram_id
                    'timestamp': row[8],        # telegram_date
                    'user_id': str(row[5]) if row[5] else "unknown"  # sender_id
                })()
                all_source_messages.append(msg)
            
            if not all_source_messages:
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
                    embedding_function=openai_ef,
                    metadata={"hnsw:space": "cosine"}
                )
            except:
                pass
            
            # Add messages to search index
            documents = []
            metadatas = []
            ids = []
            
            for message in all_source_messages:
                # Use the helper to get the best text for searching
                searchable_text = self._get_searchable_text(message, expansion_session)
                
                # Skip if there's no text to index
                if not searchable_text:
                    continue
                
                documents.append(searchable_text)
                metadatas.append({
                    "message_id": str(message.telegram_id),
                    "chat_id": str(message.chat_id),
                    "sender_name": message.sender_name or "Unknown",
                    "timestamp": str(message.telegram_date)
                })
                ids.append(str(message.telegram_id))
            
            # Batch add to collection
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Added {len(documents)} messages to search index")
        
        finally:
            source_session.close()
            expansion_session.close()
    
    async def _rewrite_query(self, original_query: str) -> str:
        """Rewrite user query to be more suitable for semantic search."""
        try:
            llm_provider = LLMFactory.create_provider("openai")
            
            system_prompt = """You are a query rewriting assistant for semantic search over Telegram messages. 
Your task is to rewrite user queries to make them more effective for finding relevant messages.

Guidelines:
- Expand abbreviations and informal language
- Add relevant synonyms and related terms
- Make implicit concepts explicit
- Keep the core intent intact
- Use natural language that would appear in casual conversation
- For Russian queries, maintain Russian language

Examples:
- "баня" → "баня сауна парение парилка релакс отдых"
- "встреча вчера" → "встреча вчера обсуждение планы договоренности"
- "project updates" → "project updates progress status development work"

Return only the rewritten query, nothing else."""

            user_prompt = f"Rewrite this query for better semantic search: {original_query}"
            
            response = await llm_provider.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            rewritten_query = response.content.strip()
            print(f"🔄 Query rewritten: '{original_query}' → '{rewritten_query}'")
            return rewritten_query
            
        except Exception as e:
            print(f"⚠️ Query rewriting failed: {e}, using original query")
            return original_query
    
    @log_tool_operation("search_relevant_messages")
    async def search_relevant_messages(self, search_input: SearchToolInput) -> SearchToolOutput:
        """Search for messages using semantic search."""
        # Rewrite query for better semantic search
        rewritten_query = await self._rewrite_query(search_input.query_text)
        
        # Build metadata filters
        where_clause = {}
        if search_input.chat_id:
            where_clause["chat_id"] = search_input.chat_id
        
        # Perform semantic search with rewritten query
        try:
            results = self.collection.query(
                query_texts=[rewritten_query],
                n_results=100,
                where=where_clause if where_clause else None,
                include=["metadatas", "distances", "documents"] if search_input.debug else ["metadatas", "distances"]
            )
        except Exception as e:
            print(f"Search error: {e}")
            return SearchToolOutput(messages=[], total_found=0)
        
        if not results["ids"] or not results["ids"][0]:
            return SearchToolOutput(messages=[], total_found=0)
        
        # Extract message_ids and scores from the results  
        # With cosine similarity: distances 0-2, where 0=identical, 2=opposite
        # Filter by distance threshold (0.75 means max cosine distance allowed)
        DISTANCE_THRESHOLD = 0.75
        message_ids = []
        message_scores = {}
        
        for i, metadata in enumerate(results["metadatas"][0]):
            message_id = metadata["message_id"]
            
            # Get cosine distance
            distance = results["distances"][0][i] if results.get("distances") else 2.0
            
            # Check distance threshold (skip if distance is too high)
            if distance > DISTANCE_THRESHOLD:
                continue  # Skip messages that are not similar enough
                
            message_ids.append(message_id)
            if search_input.debug:
                # For display, convert to similarity score (1 - distance)
                message_scores[message_id] = 1.0 - distance
        
        # Get full message details from database using raw SQL
        with self.SessionLocal() as session:
            if message_ids:
                # Convert message_ids to integers, filtering out non-numeric values
                int_message_ids = [int(mid) for mid in message_ids if mid.isdigit()]
                if int_message_ids:
                    placeholders = ','.join([f':id{i}' for i in range(len(int_message_ids))])
                    query = f"SELECT * FROM messages WHERE telegram_id IN ({placeholders})"
                    params = {f'id{i}': mid for i, mid in enumerate(int_message_ids)}
                    results = session.execute(text(query), params).fetchall()
                else:
                    results = []
                
                # Convert raw results to message objects
                db_messages = []
                for row in results:
                    msg = type('Message', (), {
                        'id': row[0],
                        'telegram_id': row[1],
                        'chat_id': row[2],
                        'text': row[3],
                        'message_type': row[4],
                        'sender_id': row[5],
                        'sender_name': row[6],
                        'sender_username': row[7],
                        'telegram_date': row[8],
                        'created_at': row[9],
                        'updated_at': row[10],
                        'is_outgoing': row[11],
                        'is_reply': row[12],
                        'reply_to_message_id': row[13],
                        'forward_from_id': row[14],
                        'forward_from_name': row[15],
                        'media_type': row[16],
                        'media_file_id': row[17],
                        'media_file_name': row[18],
                        'media_file_size': row[19],
                        # Add properties for compatibility
                        'message_id': str(row[1]),  # telegram_id
                        'timestamp': row[8],        # telegram_date
                        'user_id': str(row[5]) if row[5] else "unknown"  # sender_id
                    })()
                    db_messages.append(msg)
            else:
                db_messages = []
        
        # Convert to TelegramMessage objects and maintain search result order
        telegram_messages = []
        messages_with_scores = []
        
        # Get expansion session if in debug mode
        expansion_session = self.ExpansionSessionLocal() if search_input.debug else None
        
        try:
            for message_id in message_ids:
                for db_message in db_messages:
                    if str(db_message.telegram_id) == message_id:
                        telegram_msg = TelegramMessage(
                            message_id=str(db_message.telegram_id),
                            chat_id=str(db_message.chat_id),
                            user_id=str(db_message.sender_id) if db_message.sender_id else "unknown",
                            sender_name=db_message.sender_name or "Unknown",
                            text=db_message.text or "",
                            timestamp=db_message.telegram_date,
                            reply_to_message_id=str(db_message.reply_to_message_id) if db_message.reply_to_message_id else None
                        )
                        telegram_messages.append(telegram_msg)
                        
                        # If debug mode, get expanded text and create MessageWithScore
                        if search_input.debug:
                            from ..models.agent import MessageWithScore
                            expanded_text = None
                            if expansion_session:
                                expansion = expansion_session.query(MessageExpansion).filter(
                                    MessageExpansion.message_id == message_id
                                ).first()
                                if expansion:
                                    expanded_text = expansion.expanded_text
                            
                            messages_with_scores.append(MessageWithScore(
                                message=telegram_msg,
                                relevance_score=message_scores.get(message_id, 0.0),
                                expanded_text=expanded_text
                            ))
                        break
        finally:
            if expansion_session:
                expansion_session.close()
        
        return SearchToolOutput(
            messages=telegram_messages,
            total_found=len(telegram_messages),
            messages_with_scores=messages_with_scores if search_input.debug else None,
            rewritten_query=rewritten_query
        )


# Global instance - will be initialized when needed
search_tool = None

def get_search_tool(database_url: str = None, chroma_path: str = None, expansion_db_url: str = None):
    """Get or create the search tool instance."""
    global search_tool
    if search_tool is None:
        search_tool = MessageSearchTool(chroma_path=chroma_path, database_url=database_url, expansion_db_url=expansion_db_url)
        # Populate search index on first use
        search_tool.populate_search_index()
    return search_tool