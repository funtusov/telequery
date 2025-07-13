#!/usr/bin/env python3
"""
Simple script to load environment and run the test.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY environment variable is not set!")
    print("Please create a .env file with your OpenAI API key:")
    print("OPENAI_API_KEY=your_api_key_here")
    exit(1)

print(f"✅ OpenAI API key found: {os.getenv('OPENAI_API_KEY')[:8]}...")

# Import and run the test
from test_telequery import test_telequery
import asyncio

if __name__ == "__main__":
    asyncio.run(test_telequery())