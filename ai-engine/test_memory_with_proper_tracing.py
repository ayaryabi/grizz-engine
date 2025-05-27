#!/usr/bin/env python3
"""
Test script that properly traces both Memory Planner and Memory Actor phases
This will show both agents in the OpenAI tracing dashboard
"""

import asyncio
import os
import sys
from agents import Agent, Runner, function_tool

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import config to load .env file automatically
from app.core.config import get_settings

# Load settings (this will load the .env file)
settings = get_settings()

from app.agents.memory.memory_manager import MemoryManager

# Create a test agent that uses the memory system as a tool
@function_tool
async def memory_system_tool(user_request: str, content: str, title: str = "Untitled", content_type: str = "note") -> str:
    """Save content to memory using the full planner-actor workflow"""
    memory_manager = MemoryManager()
    
    # Add conversation context for testing
    conversation_history = [
        {"role": "user", "content": "I've been learning about AI ethics lately"},
        {"role": "assistant", "content": "That's a great topic! What aspects interest you most?"},
        {"role": "user", "content": "Mainly the impact on employment and algorithm bias"},
        {"role": "assistant", "content": "Those are crucial areas. Employment displacement and algorithmic fairness are major concerns."},
        {"role": "user", "content": "Yes, we discussed how AI could lead to job displacement in various industries"},
        {"role": "assistant", "content": "And the importance of creating unbiased algorithms through diverse data sets."},
        {"role": "user", "content": "Exactly! We also talked about the need for transparent algorithms and ethical guidelines."}
    ]
    
    result = await memory_manager.process_memory_request(
        user_request=user_request,
        content=content,
        conversation_history=conversation_history,
        latest_message=user_request,
        title=title,
        item_type=content_type
    )
    
    if result.get('success'):
        return f"✅ Successfully saved '{title}' to memory with ID: {result.get('id')}"
    else:
        return f"❌ Failed to save: {result.get('error')}"

# Create a test agent that will be traced
test_agent = Agent(
    name="Memory System Tester",
    instructions="""
    You are testing the memory system. When a user asks you to save content,
    use the memory_system_tool to process and save it.
    
    Always provide helpful feedback about what was saved.
    """,
    tools=[memory_system_tool],
    model="gpt-4o-mini"
)

async def test_with_proper_tracing():
    """Test that will show both planner and actor in traces"""
    
    print("🧪 Testing Memory System with Proper Tracing")
    print("=" * 60)
    
    # Verify API key is loaded
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    
    print(f"✅ OpenAI API Key loaded: {settings.OPENAI_API_KEY[:10]}...")
    
    # Test case: Summarization scenario (this was failing in your trace)
    print("\n🧠 Test: Conversation Summarization")
    print("-" * 40)
    
    user_request = "Summarize our discussion about AI ethics and save it for my research"
    
    # This call will go through the OpenAI Agents SDK and be properly traced
    result = await Runner.run(
        test_agent, 
        user_request
    )
    
    print("🎯 Test Agent Response:")
    print(result.final_output)
    
    print("\n" + "=" * 60)
    print("🎉 Test completed!")
    print("📊 Check your OpenAI dashboard for complete trace including:")
    print("   1. Test Agent (main agent)")
    print("   2. memory_system_tool execution") 
    print("   3. Memory Planner Agent (planning phase)")
    print("   4. Memory Actor Agent (execution phase)")
    print("   5. All sub-tools (summarization, categorization, etc.)")

if __name__ == "__main__":
    try:
        asyncio.run(test_with_proper_tracing())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc() 