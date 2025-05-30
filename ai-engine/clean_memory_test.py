#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.base_agent import BaseGrizzAgent
from app.agents.memory.master_memory_agent import save_memory_content
from agents import Runner

async def test_memory_like_chat_agent():
    """Test memory system the same way chat_agent.py uses it"""
    
    print("🧪 Clean Memory Test (Chat Agent Style)")
    print("=" * 50)
    
    # Create agent exactly like chat_agent.py does
    test_agent = BaseGrizzAgent(
        name="Memory Test Agent",
        instructions="You are a helpful assistant that can save content to memory. When users ask you to save something, use the save_memory_content tool.",
        tools=[save_memory_content],  # Same as chat_agent.py
        llm_type="chat"  # Same as chat_agent.py
    )
    
    # Test message
    test_message = """
Hey, can you save this note about Python for me?

# Python Programming Tips

Python is a powerful programming language that's great for:
- Web development with frameworks like Django and Flask
- Data science and machine learning with libraries like pandas and scikit-learn
- Automation and scripting
- API development

Key Python concepts:
- Object-oriented programming
- List comprehensions
- Decorators
- Context managers

This is useful for my coding projects!
"""
    
    print(f"📝 Testing memory save functionality")
    print(f"📏 Message length: {len(test_message)} characters")
    print("\n🚀 Running test agent...")
    
    try:
        result = await Runner.run(test_agent, test_message)
        print(f"✅ Test completed!")
        print(f"📋 Result: {result.final_output}")
        
        # Check if memory was saved successfully
        result_text = str(result.final_output)
        if "Memory Saved Successfully" in result_text or "saved" in result_text.lower():
            print("🎉 SUCCESS: Memory tool worked!")
            return True
        else:
            print("⚠️  WARNING: Tool ran but unclear if saved")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_memory_like_chat_agent())
    if success:
        print("\n🎉 CLEAN TEST PASSED - Memory works like chat_agent!")
    else:
        print("\n💥 CLEAN TEST FAILED - Need to fix memory system") 