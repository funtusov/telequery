import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.database import TelegramMessage
from ..models.schema import Message as SourceMessage
from ..database.expansion_schema import MessageExpansion
from ..llm.factory import LLMFactory, LLMProvider

def _to_datetime(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        # Handle different string formats, including ISO 8601
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

class MessageContextualizer:
    def __init__(self, source_session: Session, expansion_session: Session):
        self.source_session = source_session
        self.expansion_session = expansion_session
        self.llm_provider: LLMProvider = LLMFactory.create_provider()

    def _get_batch_with_context(self, messages: List[SourceMessage], context_window: int = 10) -> List[SourceMessage]:
        """Get messages with additional context before the batch for better expansions."""
        if not messages:
            return []
        
        # Get the earliest message in the batch
        earliest_message = min(messages, key=lambda m: m.timestamp)
        
        # Get context messages before the batch using raw SQL
        results = self.source_session.execute(
            text("SELECT * FROM messages WHERE chat_id = :chat_id AND telegram_date < :telegram_date ORDER BY telegram_date DESC LIMIT :limit"),
            {"chat_id": earliest_message.chat_id, "telegram_date": earliest_message.telegram_date, "limit": context_window}
        ).fetchall()
        
        # Convert raw results to message objects
        context_messages = []
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
            context_messages.append(msg)
        
        # Combine context and batch messages, sorted chronologically
        all_messages = list(reversed(context_messages)) + sorted(messages, key=lambda m: m.telegram_date)
        return all_messages

    def _create_batch_expansion_prompt(self, batch_messages: List[SourceMessage], context_messages: List[SourceMessage]) -> str:
        """Creates a prompt for expanding a batch of messages."""
        
        # Format all messages (context + batch) in the specified format
        all_messages = context_messages + batch_messages
        messages_str = ""
        
        for msg in all_messages:
            messages_str += f"message_id: {msg.message_id}\n"
            messages_str += f"author: {msg.sender_name}\n"
            messages_str += f"original_text: {msg.text}\n"
            messages_str += "---\n"
        
        # Create a list of message IDs to expand (only the batch messages, not context)
        batch_ids = [msg.message_id for msg in batch_messages]
        
        prompt = f"""
You are processing a chat chunk of Telegram messages to make them searchable. You will be given a conversation with multiple messages and need to expand specific messages to be self-contained by incorporating relevant context from the conversation.

Here is the chat chunk:

{messages_str}

Expand the following message IDs to include all necessary context so they can be understood standalone: {', '.join(batch_ids)}

Rules:
1. Only use information from the provided conversation
2. Do not add new information or make assumptions
3. Keep the original message's intent and tone
4. Make it a complete, searchable sentence or paragraph
5. If a message is already self-contained, you may keep it mostly unchanged

Return your response as a JSON object with this exact structure:
{{
  "expansions": [
    {{
      "message_id": "exact_message_id_here",
      "original_text": "original message text",
      "expanded_text": "rewritten self-contained version"
    }}
  ]
}}

Only include expansions for the specified message IDs. Ensure the JSON is valid.
"""
        return prompt

    async def expand_batch_and_save(self, batch_messages: List[SourceMessage]):
        """Process a batch of messages and save their expansions."""
        if not batch_messages:
            return 0
        
        # Filter out messages without text
        valid_messages = [msg for msg in batch_messages if msg.text and msg.text.strip()]
        if not valid_messages:
            return 0
        
        # Get context for the batch
        context_messages = self._get_batch_with_context(valid_messages)
        
        # Create the batch expansion prompt
        user_prompt = self._create_batch_expansion_prompt(valid_messages, context_messages)
        
        system_prompt = "You are an AI assistant that rewrites Telegram messages to include conversational context, making them standalone and searchable. Always respond with valid JSON."
        
        try:
            # Generate expansions for the entire batch
            response = await self.llm_provider.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                expansions_data = json.loads(response.content)
                expansions = expansions_data.get("expansions", [])
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"Response content: {response.content[:500]}...")
                return 0
            
            # Save expansions to database
            saved_count = 0
            for expansion_data in expansions:
                try:
                    message_id = str(expansion_data["message_id"])
                    
                    # Check if expansion already exists
                    existing = self.expansion_session.query(MessageExpansion).filter_by(
                        message_id=message_id
                    ).first()
                    
                    if existing:
                        # Skip if already exists
                        continue
                    
                    expansion = MessageExpansion(
                        message_id=message_id,
                        expanded_text=expansion_data["expanded_text"],
                        model_used=response.model
                    )
                    self.expansion_session.add(expansion)
                    saved_count += 1
                except Exception as e:
                    print(f"❌ Error saving expansion for {expansion_data.get('message_id', 'unknown')}: {e}")
                    continue
            
            # Commit all expansions
            self.expansion_session.commit()
            return saved_count
            
        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            return 0

    # Keep the old method for backward compatibility
    async def expand_and_save_message(self, message: TelegramMessage):
        """Legacy method - now uses batch processing with single message."""
        # Convert to SourceMessage for batch processing using raw SQL
        result = self.source_session.execute(
            text("SELECT * FROM messages WHERE telegram_id = :telegram_id"),
            {"telegram_id": int(message.message_id)}
        ).fetchone()
        
        if result:
            source_message = type('Message', (), {
                'id': result[0],
                'telegram_id': result[1],
                'chat_id': result[2],
                'text': result[3],
                'message_type': result[4],
                'sender_id': result[5],
                'sender_name': result[6],
                'sender_username': result[7],
                'telegram_date': _to_datetime(result[8]),
                'created_at': _to_datetime(result[9]),
                'updated_at': _to_datetime(result[10]),
                'is_outgoing': result[11],
                'is_reply': result[12],
                'reply_to_message_id': result[13],
                'forward_from_id': result[14],
                'forward_from_name': result[15],
                'media_type': result[16],
                'media_file_id': result[17],
                'media_file_name': result[18],
                'media_file_size': result[19],
                # Add properties for compatibility
                'message_id': str(result[1]),  # telegram_id
                'timestamp': _to_datetime(result[8]),        # telegram_date
                'user_id': str(result[5]) if result[5] else "unknown"  # sender_id
            })()
        else:
            source_message = None
        
        if source_message:
            await self.expand_batch_and_save([source_message])