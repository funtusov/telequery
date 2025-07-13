#!/usr/bin/env python3
"""
Test script for Telequery AI.
This script will:
1. Initialize the database
2. Populate with sample data
3. Start the FastAPI server
4. Test query functionality
"""

import asyncio
import httpx
import time
import subprocess
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database.init_db import init_database


async def test_telequery():
    """Test the Telequery AI system end-to-end."""
    
    print("🚀 Starting Telequery AI Test")
    print("=" * 50)
    
    # Step 1: Initialize database
    print("📦 Initializing database...")
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Step 2: Populate sample data
    print("\n📝 Populating sample data...")
    try:
        # Run the populate script
        result = subprocess.run([
            sys.executable, "scripts/populate_sample_data.py"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Sample data populated successfully")
            print(result.stdout)
        else:
            print(f"❌ Sample data population failed: {result.stderr}")
            return
    except Exception as e:
        print(f"❌ Sample data population failed: {e}")
        return
    
    # Step 3: Start FastAPI server in background
    print("\n🌐 Starting FastAPI server...")
    server_process = None
    try:
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        await asyncio.sleep(5)
        
        # Test if server is running
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/status")
                if response.status_code == 200:
                    print("✅ Server started successfully")
                    print(f"📊 Status response: {response.json()}")
                else:
                    print(f"❌ Server status check failed: {response.status_code}")
                    return
            except Exception as e:
                print(f"❌ Server connection failed: {e}")
                return
    
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return
    
    # Step 4: Test query functionality
    print("\n🔍 Testing query functionality...")
    
    test_queries = [
        "who takes care of electricity for the camp?",
        "what about water systems?", 
        "who is handling food storage?",
        "what did Dave suggest about connectivity?"
    ]
    
    async with httpx.AsyncClient() as client:
        for query in test_queries:
            print(f"\n❓ Testing query: '{query}'")
            
            try:
                response = await client.post(
                    "http://localhost:8000/query",
                    json={
                        "user_question": query,
                        "telegram_user_id": "test_user_123",
                        "telegram_chat_id": "group_camp_planning"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Query successful!")
                    print(f"📄 Answer: {result['answer_text']}")
                    print(f"📚 Sources: {len(result['source_messages'])} messages")
                    print(f"🎯 Status: {result['status']}")
                    
                    if result['source_messages']:
                        print("📋 Source messages:")
                        for msg in result['source_messages'][:2]:  # Show first 2
                            print(f"  - {msg['sender']} ({msg['timestamp'][:10]}): {msg['text'][:100]}...")
                else:
                    print(f"❌ Query failed with status: {response.status_code}")
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Query request failed: {e}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    if server_process:
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_telequery())