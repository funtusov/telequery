"""Script to populate the database with sample Telegram messages for testing."""
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.connection import SessionLocal
from src.models.schema import Message
from src.models.database import TelegramMessage
from src.tools.search import get_search_tool


def create_sample_messages():
    """Create sample messages for testing."""
    sample_messages = [
        {
            "message_id": "msg_001",
            "chat_id": "group_camp_planning",
            "user_id": "alice_123",
            "sender_name": "Alice",
            "text": "Hey everyone, just confirming I've got the main generator covered for our camp's electricity. I'll map out the power grid plan this weekend.",
            "timestamp": datetime.now() - timedelta(days=15),
            "reply_to_message_id": None
        },
        {
            "message_id": "msg_002", 
            "chat_id": "group_camp_planning",
            "user_id": "bob_456",
            "sender_name": "Bob",
            "text": "Thanks Alice! I'll handle the water pumps and filtration system. Already ordered the equipment.",
            "timestamp": datetime.now() - timedelta(days=14),
            "reply_to_message_id": "msg_001"
        },
        {
            "message_id": "msg_003",
            "chat_id": "group_camp_planning", 
            "user_id": "carol_789",
            "sender_name": "Carol",
            "text": "What about food storage? I can bring a few coolers but we'll need ice delivery.",
            "timestamp": datetime.now() - timedelta(days=13),
            "reply_to_message_id": None
        },
        {
            "message_id": "msg_004",
            "chat_id": "group_camp_planning",
            "user_id": "alice_123", 
            "sender_name": "Alice",
            "text": "Good point Carol. I'll contact the local ice company for daily deliveries.",
            "timestamp": datetime.now() - timedelta(days=12),
            "reply_to_message_id": "msg_003"
        },
        {
            "message_id": "msg_005",
            "chat_id": "group_camp_planning",
            "user_id": "dave_101",
            "sender_name": "Dave",
            "text": "Has anyone thought about wifi? I can set up a starlink connection if needed.",
            "timestamp": datetime.now() - timedelta(days=10),
            "reply_to_message_id": None
        }
    ]
    
    return sample_messages


def populate_database():
    """Populate the database with sample data."""
    print("Creating sample messages...")
    
    with SessionLocal() as db:
        # Clear existing data
        db.query(Message).delete()
        db.commit()
        
        # Add sample messages
        sample_data = create_sample_messages()
        
        for msg_data in sample_data:
            message = Message(**msg_data)
            db.add(message)
        
        db.commit()
        print(f"Added {len(sample_data)} sample messages to database")
    
    # Add messages to vector index
    print("Adding messages to vector search index...")
    
    with SessionLocal() as db:
        messages = db.query(Message).all()
        
        for db_msg in messages:
            telegram_msg = TelegramMessage(
                message_id=db_msg.message_id,
                chat_id=db_msg.chat_id,
                user_id=db_msg.user_id,
                sender_name=db_msg.sender_name,
                text=db_msg.text,
                timestamp=db_msg.timestamp,
                reply_to_message_id=db_msg.reply_to_message_id
            )
            
            get_search_tool().add_message_to_index(telegram_msg)
    
    print("Sample data population complete!")


if __name__ == "__main__":
    populate_database()