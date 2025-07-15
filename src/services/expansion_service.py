import asyncio
import os
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..models.schema import Message as SourceMessage
from ..database.expansion_schema import MessageExpansion, Base
from ..indexing.contextualizer import MessageContextualizer
from ..models.database import TelegramMessage


def _to_datetime(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        # Handle different string formats, including ISO 8601
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

class ExpansionService:
    """Service for automatically processing message expansions."""
    
    def __init__(self, database_url: str, expansion_db_path: str):
        self.database_url = database_url
        self.expansion_db_path = expansion_db_path
        
        # Create database engines
        self.source_engine = create_engine(database_url)
        self.expansion_engine = create_engine(f"sqlite:///{expansion_db_path}")
        
        # Create session makers
        self.SourceSession = sessionmaker(bind=self.source_engine)
        self.ExpansionSession = sessionmaker(bind=self.expansion_engine)
        
        # Ensure expansion database exists
        self._ensure_expansion_database()
    
    def _ensure_expansion_database(self):
        """Create expansion database and tables if they don't exist."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.expansion_db_path), exist_ok=True)
        
        # Create tables
        Base.metadata.create_all(self.expansion_engine)
        print(f"✅ Expansion database initialized at: {self.expansion_db_path}")
    
    async def process_new_messages(self, batch_size: int = 50) -> int:
        """
        Process new messages in batches that haven't been expanded yet.
        Uses overlapping batches for better context continuity.
        Returns the number of messages processed.
        """
        source_session = self.SourceSession()
        expansion_session = self.ExpansionSession()
        
        try:
            # Find which message IDs have already been processed
            processed_ids_query = expansion_session.query(MessageExpansion.message_id).all()
            processed_ids = {pid[0] for pid in processed_ids_query}
            
            print(f"📊 Found {len(processed_ids)} already expanded messages")
            
            # Find new messages that need expansion using raw SQL
            # Always fetch all messages and filter in memory to avoid SQL parameter limits
            all_messages_query = text("SELECT * FROM messages WHERE text IS NOT NULL AND text != '' ORDER BY telegram_date ASC")
            all_results = source_session.execute(all_messages_query).fetchall()
            
            # Filter out processed messages
            if processed_ids:
                results = [row for row in all_results if str(row[1]) not in processed_ids]
            else:
                results = all_results
            
            # Convert raw results to SourceMessage objects
            new_messages = []
            for row in results:
                # Create a simple object with the needed attributes
                msg = type('Message', (), {
                    'id': row[0],
                    'telegram_id': row[1],
                    'chat_id': row[2],
                    'text': row[3],
                    'message_type': row[4],
                    'sender_id': row[5],
                    'sender_name': row[6],
                    'sender_username': row[7],
                    'telegram_date': _to_datetime(row[8]),
                    'created_at': _to_datetime(row[9]),
                    'updated_at': _to_datetime(row[10]),
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
                    'timestamp': _to_datetime(row[8]),        # telegram_date
                    'user_id': str(row[5]) if row[5] else "unknown"  # sender_id
                })()
                new_messages.append(msg)
            
            if not new_messages:
                print("✅ No new messages to expand")
                return 0
            
            print(f"🔄 Processing {len(new_messages)} new messages in batches of {batch_size}...")
            
            contextualizer = MessageContextualizer(source_session, expansion_session)
            total_processed = 0
            
            # Process messages in overlapping batches
            overlap_size = min(10, batch_size // 5)  # 10 messages overlap or 20% of batch size
            batch_start = 0
            
            while batch_start < len(new_messages):
                # Get current batch
                batch_end = min(batch_start + batch_size, len(new_messages))
                current_batch = new_messages[batch_start:batch_end]
                
                if not current_batch:
                    break
                
                print(f"🔄 Processing batch {batch_start}-{batch_end-1} ({len(current_batch)} messages)...")
                
                try:
                    # Process the entire batch at once
                    processed_count = await contextualizer.expand_batch_and_save(current_batch)
                    total_processed += processed_count
                    
                    print(f"✅ Batch completed: {processed_count}/{len(current_batch)} messages processed")
                    
                except Exception as e:
                    print(f"❌ Error processing batch {batch_start}-{batch_end-1}: {e}")
                    # Continue with next batch even if this one fails
                
                # Move to next batch with overlap
                if batch_end >= len(new_messages):
                    break  # We've processed all messages
                
                batch_start = batch_end - overlap_size
                
                # Ensure we don't go backwards
                if batch_start <= 0:
                    batch_start = batch_end
            
            print(f"✅ Successfully processed {total_processed} messages across all batches")
            return total_processed
            
        finally:
            source_session.close()
            expansion_session.close()
    
    async def get_expansion_stats(self) -> dict:
        """Get statistics about the expansion database."""
        source_session = self.SourceSession()
        expansion_session = self.ExpansionSession()
        
        try:
            # Count total messages in source database using raw SQL
            total_messages = source_session.execute(
                text("SELECT COUNT(*) FROM messages WHERE text IS NOT NULL AND text != ''")
            ).scalar()
            
            # Count expanded messages
            expanded_messages = expansion_session.query(MessageExpansion).count()
            
            return {
                "total_messages": total_messages,
                "expanded_messages": expanded_messages,
                "pending_messages": total_messages - expanded_messages,
                "completion_percentage": (expanded_messages / total_messages * 100) if total_messages > 0 else 0
            }
            
        finally:
            source_session.close()
            expansion_session.close()


# Global service instance
_expansion_service: Optional[ExpansionService] = None


def get_expansion_service() -> ExpansionService:
    """Get or create the expansion service instance."""
    global _expansion_service
    
    if _expansion_service is None:
        # Handle database URL with support for MAIN_DB_PATH
        main_db_path = os.getenv("MAIN_DB_PATH")
        if main_db_path:
            database_url = f"sqlite:///{main_db_path}"
        else:
            database_url = os.getenv("DATABASE_URL", "sqlite:///../telequery_db/telegram_messages.db")
        
        expansion_db_path = os.getenv("EXPANSION_DB_PATH", "../telequery_db/telequery_expansions.db")
        
        _expansion_service = ExpansionService(
            database_url=database_url,
            expansion_db_path=expansion_db_path
        )
    
    return _expansion_service


async def startup_expansion_check():
    """
    Run expansion check during server startup.
    This processes new messages automatically.
    """
    print("🚀 Starting expansion service check...")
    
    try:
        service = get_expansion_service()
        
        # Log database paths
        print(f"🔍 Main DB path: {service.database_url}")
        print(f"🔍 Expansion DB path: {service.expansion_db_path}")
        
        # Get current stats
        stats = await service.get_expansion_stats()
        print(f"📊 Expansion stats: {stats['expanded_messages']}/{stats['total_messages']} messages expanded ({stats['completion_percentage']:.1f}%)")
        
        # Process new messages if any
        if stats['pending_messages'] > 0:
            print(f"🔄 Processing {stats['pending_messages']} new messages...")
            processed = await service.process_new_messages(batch_size=50)
            print(f"✅ Expansion service processed {processed} messages")
        else:
            print("✅ All messages are already expanded")
            
    except Exception as e:
        print(f"❌ Error during expansion service startup: {e}")
        import traceback
        traceback.print_exc()