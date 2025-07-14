#!/usr/bin/env python3
import asyncio
import os
from src.agent.telequery_agent import TelequeryAgent
from src.models.agent import AgentContext

async def test_query():
    # Set up environment
    os.environ["DATABASE_URL"] = "sqlite:///./tmp/telegram_messages.db"
    os.environ["CHROMA_PATH"] = "./tmp/chroma_db"
    
    # Create agent
    agent = TelequeryAgent(
        database_url="sqlite:///./tmp/telegram_messages.db",
        chroma_path="./tmp/chroma_db"
    )
    
    # Create context
    context = AgentContext(
        user_question="Что мы решили насчёт бани?",
        telegram_user_id="default_user",
        telegram_chat_id=None
    )
    
    # Process query
    try:
        response = await agent.process_query(context)
        print(f"Status: {response.status}")
        print(f"Answer: {response.answer_text}")
        print(f"Sources: {len(response.source_messages)}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())