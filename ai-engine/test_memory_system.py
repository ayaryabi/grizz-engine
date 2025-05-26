#!/usr/bin/env python3
"""
Test script for the memory system
Run this to verify the planner-actor memory workflow works correctly
"""

import asyncio
import os
import sys

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import config to load .env file automatically
from app.core.config import get_settings

# Load settings (this will load the .env file)
settings = get_settings()

from app.agents.memory.memory_manager import MemoryManager

async def test_memory_system():
    """Test the complete memory system workflow"""
    
    print("🧪 Testing Memory System")
    print("=" * 50)
    
    # Verify API key is loaded
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        print("Please check your ai-engine/.env file")
        return
    
    print(f"✅ OpenAI API Key loaded: {settings.OPENAI_API_KEY[:10]}...")
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Test case 1: YouTube video transcript
    print("\n📺 Test 1: YouTube Video Transcript")
    print("-" * 30)
    
    test_content = """
    Welcome to this Python tutorial. Today we're going to learn about async programming.
    
    First, let's understand what async means. Async programming allows us to write 
    concurrent code using the async/await syntax.
    
    Here's a simple example:
    
    async def hello():
        print("Hello")
        await asyncio.sleep(1)
        print("World")
    
    The key benefits of async programming are:
    1. Better performance for I/O bound tasks
    2. More efficient resource usage
    3. Better user experience
    
    That's all for today's tutorial!
    """
    
    result = await memory_manager.process_memory_request(
        user_request="Save this Python async programming tutorial for my coding studies",
        content=test_content,
        title="Python Async Programming Tutorial",
        item_type="youtube_video"
    )
    
    print("Result:")
    print(result)
    
    print("\n" + "=" * 50)
    print("🎉 Memory system test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_memory_system())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 