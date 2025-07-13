#!/usr/bin/env python3
import sqlite3
import sys
from typing import List, Dict, Optional
from datetime import datetime

class InteractiveTelegramExplorer:
    def __init__(self, db_path: str = "tmp/telegram_messages.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
    def show_menu(self):
        print("\n" + "="*60)
        print("Telegram Database Explorer")
        print("="*60)
        print("1. Show database statistics")
        print("2. List all chats")
        print("3. Show recent messages")
        print("4. Search messages by text")
        print("5. Search messages by sender")
        print("6. Show messages from specific chat")
        print("7. Export messages to file")
        print("0. Exit")
        print("-"*60)
        
    def get_stats(self):
        cursor = self.conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chats")
        total_chats = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(telegram_date), MAX(telegram_date) FROM messages")
        date_range = cursor.fetchone()
        
        # Top senders
        cursor.execute("""
            SELECT sender_name, COUNT(*) as count 
            FROM messages 
            WHERE sender_name IS NOT NULL 
            GROUP BY sender_name 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_senders = cursor.fetchall()
        
        print(f"\nTotal messages: {total_messages:,}")
        print(f"Total chats: {total_chats}")
        print(f"Date range: {date_range[0]} to {date_range[1]}")
        print("\nTop 5 senders:")
        for sender in top_senders:
            print(f"  - {sender['sender_name']}: {sender['count']:,} messages")
            
    def list_chats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, chat_type, username FROM chats ORDER BY name")
        chats = cursor.fetchall()
        
        print(f"\nFound {len(chats)} chats:")
        for chat in chats:
            username = f" (@{chat['username']})" if chat['username'] else ""
            print(f"  [{chat['id']}] {chat['name']}{username} - {chat['chat_type']}")
            
    def show_recent_messages(self):
        count = input("\nHow many recent messages to show? (default: 10): ").strip()
        count = int(count) if count else 10
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as chat_name 
            FROM messages m 
            JOIN chats c ON m.chat_id = c.id 
            ORDER BY m.telegram_date DESC 
            LIMIT ?
        """, (count,))
        
        self._display_messages(cursor.fetchall())
        
    def search_by_text(self):
        query = input("\nEnter search text: ").strip()
        if not query:
            print("No search query provided.")
            return
            
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as chat_name 
            FROM messages m 
            JOIN chats c ON m.chat_id = c.id 
            WHERE m.text LIKE ? 
            ORDER BY m.telegram_date DESC 
            LIMIT 50
        """, (f'%{query}%',))
        
        results = cursor.fetchall()
        print(f"\nFound {len(results)} messages containing '{query}':")
        self._display_messages(results)
        
    def search_by_sender(self):
        sender = input("\nEnter sender name: ").strip()
        if not sender:
            print("No sender name provided.")
            return
            
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as chat_name 
            FROM messages m 
            JOIN chats c ON m.chat_id = c.id 
            WHERE m.sender_name LIKE ? 
            ORDER BY m.telegram_date DESC 
            LIMIT 50
        """, (f'%{sender}%',))
        
        results = cursor.fetchall()
        print(f"\nFound {len(results)} messages from '{sender}':")
        self._display_messages(results)
        
    def show_chat_messages(self):
        self.list_chats()
        chat_id = input("\nEnter chat ID: ").strip()
        if not chat_id.isdigit():
            print("Invalid chat ID.")
            return
            
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as chat_name 
            FROM messages m 
            JOIN chats c ON m.chat_id = c.id 
            WHERE m.chat_id = ? 
            ORDER BY m.telegram_date DESC 
            LIMIT 50
        """, (int(chat_id),))
        
        self._display_messages(cursor.fetchall())
        
    def export_messages(self):
        filename = input("\nEnter output filename (default: telegram_export.txt): ").strip()
        filename = filename or "telegram_export.txt"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as chat_name 
            FROM messages m 
            JOIN chats c ON m.chat_id = c.id 
            ORDER BY m.telegram_date
        """)
        
        with open(filename, 'w', encoding='utf-8') as f:
            count = 0
            for msg in cursor:
                count += 1
                f.write(f"[{msg['telegram_date']}] {msg['chat_name']}\n")
                f.write(f"{msg['sender_name'] or 'Unknown'}: {msg['text'] or '[No text]'}\n")
                f.write("-" * 80 + "\n")
                
        print(f"Exported {count} messages to {filename}")
        
    def _display_messages(self, messages):
        for msg in messages:
            print(f"\n[{msg['telegram_date']}] {msg['chat_name']}")
            print(f"{msg['sender_name'] or 'Unknown'}: ", end='')
            
            text = msg['text'] or '[No text]'
            if len(text) > 150:
                text = text[:150] + '...'
            print(text)
            
            if msg['media_type']:
                print(f"[Media: {msg['media_type']}]")
                
    def run(self):
        while True:
            self.show_menu()
            choice = input("Enter your choice: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                self.get_stats()
            elif choice == '2':
                self.list_chats()
            elif choice == '3':
                self.show_recent_messages()
            elif choice == '4':
                self.search_by_text()
            elif choice == '5':
                self.search_by_sender()
            elif choice == '6':
                self.show_chat_messages()
            elif choice == '7':
                self.export_messages()
            else:
                print("Invalid choice. Please try again.")
                
            input("\nPress Enter to continue...")
            
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    explorer = InteractiveTelegramExplorer()
    try:
        explorer.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)