#!/usr/bin/env python3
"""
Super Simple Memory Test - Just save content, no fancy stuff
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.agents.memory.memory_manager import MemoryManager

settings = get_settings()

async def save_content(content: str):
    """Save content using memory system"""
    print(f"💾 Saving: {content}")
    print(f"📏 Length: {len(content)} characters")
    
    memory_manager = MemoryManager()
    
    try:
        result = await memory_manager.process_memory_request(
            user_request="Save this content",
            content=content,
            title="Test Content",
            item_type="note"
        )
        
        if result.get("success"):
            print(f"✅ SUCCESS!")
            print(f"   Title: {result.get('title', 'Unknown')}")
            print(f"   ID: {result.get('id', 'Unknown')}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

async def main():
    print("🧠 SIMPLE MEMORY TEST")
    print("=" * 40)
    
    # Check API key
    if not settings.OPENAI_API_KEY:
        print("❌ No OpenAI API key found")
        return
    
    print(f"✅ API Key loaded: {settings.OPENAI_API_KEY[:10]}...")
    print()
    
    while True:
        print("Enter content to save (or 'quit'):")
        content = input("➤ ").strip()
        
        if content.lower() == 'quit':
            break
            
        if content:
            print()
            await save_content(content)
            print()
        
if __name__ == "__main__":
    asyncio.run(main()) 