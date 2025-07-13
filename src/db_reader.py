import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import argparse


class TelegramDBReader:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def get_all_chats(self) -> List[Dict]:
        """Get all chats from the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, telegram_id, name, username, chat_type, 
                   is_verified, is_scam, is_fake, created_at
            FROM chats
            ORDER BY name
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_messages_by_chat(self, chat_id: int, limit: int = 10) -> List[Dict]:
        """Get messages from a specific chat."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.id, m.telegram_id, m.text, m.sender_name, 
                   m.sender_username, m.telegram_date, m.is_outgoing,
                   m.media_type, c.name as chat_name
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE m.chat_id = ?
            ORDER BY m.telegram_date DESC
            LIMIT ?
        """, (chat_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def search_messages(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Search messages by text content."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.id, m.text, m.sender_name, m.telegram_date,
                   c.name as chat_name, c.chat_type
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE m.text LIKE ?
            ORDER BY m.telegram_date DESC
            LIMIT ?
        """, (f'%{search_term}%', limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_messages_by_sender(self, sender_name: str, limit: int = 20) -> List[Dict]:
        """Get messages from a specific sender."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.id, m.text, m.sender_name, m.telegram_date,
                   c.name as chat_name
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            WHERE m.sender_name LIKE ?
            ORDER BY m.telegram_date DESC
            LIMIT ?
        """, (f'%{sender_name}%', limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_messages(self, limit: int = 20) -> List[Dict]:
        """Get most recent messages across all chats."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.id, m.text, m.sender_name, m.telegram_date,
                   c.name as chat_name, c.chat_type
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            ORDER BY m.telegram_date DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = cursor.fetchone()[0]
        
        # Total chats
        cursor.execute("SELECT COUNT(*) FROM chats")
        stats['total_chats'] = cursor.fetchone()[0]
        
        # Messages by chat type
        cursor.execute("""
            SELECT c.chat_type, COUNT(m.id) as count
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            GROUP BY c.chat_type
        """)
        stats['messages_by_chat_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Date range
        cursor.execute("""
            SELECT MIN(telegram_date) as earliest, MAX(telegram_date) as latest
            FROM messages
        """)
        row = cursor.fetchone()
        stats['date_range'] = {
            'earliest': row[0],
            'latest': row[1]
        }
        
        # Top senders
        cursor.execute("""
            SELECT sender_name, COUNT(*) as count
            FROM messages
            WHERE sender_name IS NOT NULL
            GROUP BY sender_name
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_senders'] = [(row[0], row[1]) for row in cursor.fetchall()]
        
        return stats


def format_message(msg: Dict) -> str:
    """Format a message for display."""
    date = msg.get('telegram_date', 'Unknown date')
    sender = msg.get('sender_name', 'Unknown sender')
    chat = msg.get('chat_name', 'Unknown chat')
    text = msg.get('text', '')
    
    # Truncate long messages
    if text and len(text) > 200:
        text = text[:200] + '...'
    
    return f"""
[{date}] {chat}
{sender}: {text}
{'─' * 80}"""


def main():
    parser = argparse.ArgumentParser(description='Read Telegram messages from SQLite database')
    parser.add_argument('--db', default='tmp/telegram_messages.db', help='Database path')
    parser.add_argument('--action', choices=['stats', 'recent', 'search', 'chats', 'sender'], 
                       default='stats', help='Action to perform')
    parser.add_argument('--query', help='Search query or sender name')
    parser.add_argument('--limit', type=int, default=10, help='Number of results to show')
    parser.add_argument('--chat-id', type=int, help='Chat ID for specific chat messages')
    
    args = parser.parse_args()
    
    with TelegramDBReader(args.db) as reader:
        if args.action == 'stats':
            stats = reader.get_database_stats()
            print("\n📊 Database Statistics:")
            print(f"Total messages: {stats['total_messages']:,}")
            print(f"Total chats: {stats['total_chats']:,}")
            print(f"\nMessages by chat type:")
            for chat_type, count in stats['messages_by_chat_type'].items():
                print(f"  {chat_type}: {count:,}")
            print(f"\nDate range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
            print(f"\nTop 10 senders:")
            for sender, count in stats['top_senders']:
                print(f"  {sender}: {count:,} messages")
        
        elif args.action == 'recent':
            messages = reader.get_recent_messages(args.limit)
            print(f"\n📬 {len(messages)} Most Recent Messages:")
            for msg in messages:
                print(format_message(msg))
        
        elif args.action == 'search':
            if not args.query:
                print("Error: --query required for search action")
                return
            messages = reader.search_messages(args.query, args.limit)
            print(f"\n🔍 Found {len(messages)} messages containing '{args.query}':")
            for msg in messages:
                print(format_message(msg))
        
        elif args.action == 'chats':
            chats = reader.get_all_chats()
            print(f"\n💬 {len(chats)} Chats:")
            for chat in chats:
                print(f"  [{chat['id']}] {chat['name']} ({chat['chat_type']})")
        
        elif args.action == 'sender':
            if not args.query:
                print("Error: --query required for sender action")
                return
            messages = reader.get_messages_by_sender(args.query, args.limit)
            print(f"\n👤 Found {len(messages)} messages from '{args.query}':")
            for msg in messages:
                print(format_message(msg))


if __name__ == "__main__":
    main()