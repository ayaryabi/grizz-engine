#!/usr/bin/env python3
"""
Simple test for Memory Agent as Tool functionality
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from agents import Agent, Runner
from app.agents.memory.master_memory_agent import memory_tool_wrapper

async def main():
    """Test the memory agent as a tool with one simple test"""
    
    print("🧪 Testing Memory Agent as Tool\n")
    
    # Get the memory tool from the wrapper
    memory_tool = memory_tool_wrapper.as_tool()
    
    # Create a simple test agent
    test_agent = Agent(
        name="Test Agent",
        instructions="You help users save information using the memory tool.",
        tools=[memory_tool]
    )
    
    # One simple test
    test_input = "Please save this content: 'OpenAI Agents SDK is great for building multi-agent workflows' with the title 'SDK Notes'"
    
    print(f"📝 Test: {test_input}")
    print("🤖 Response:")
    
    try:
        result = await Runner.run(test_agent, test_input)
        print(result.final_output)
        print("\n✅ Test completed!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 