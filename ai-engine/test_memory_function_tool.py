#!/usr/bin/env python3
"""
Test script to verify the @function_tool approach works with planner→actor workflow
Run this to test memory functionality in isolation
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from agents import Agent, Runner, function_tool
from app.agents.memory.memory_manager import MemoryManager

# Create memory manager instance
memory_manager = MemoryManager()

@function_tool
async def test_memory_save(input: str) -> str:
    """Save and organize information into memory with proper categorization and formatting."""
    print(f"🧪 TESTING: Function tool called with input: {input}")
    
    try:
        # This should trigger the planner→actor workflow
        result = await memory_manager.process_memory_request(
            user_request=input,
            content=input,
            title="Test Memory Request",
            item_type="note"
        )
        
        print(f"🧪 TESTING: Memory workflow result: {result}")
        
        # Format the response from the planner→actor workflow
        if result.get('success'):
            return f"""**Memory Saved Successfully!**

- **Category**: {result.get('category', 'General')}
- **Content**: {result.get('title', 'Test Content')}
- **Memory ID**: {result.get('id', 'No ID')}
- **Tags**: {', '.join(result.get('tags', []))}

Status: {result.get('execution_summary', 'Memory saved successfully.')}"""
        else:
            return f"❌ Memory operation failed: {result.get('error', 'Unknown error occurred')}"
                
    except Exception as e:
        print(f"🧪 TESTING: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"❌ Memory operation error: {str(e)}"

async def main():
    """Test the memory function tool with a test agent"""
    
    print("🧪 TESTING: Creating test agent with memory function tool...")
    
    # Create a simple test agent with our memory tool
    test_agent = Agent(
        name="Memory Test Agent",
        instructions="You help users save information using the memory tool. When they want to save something, use the test_memory_save tool.",
        tools=[test_memory_save]
    )
    
    print("🧪 TESTING: Agent created successfully")
    print(f"🧪 TESTING: Agent has {len(test_agent.tools)} tools")
    
    # Test input
    test_input = "Save this business idea: AI-powered fitness community platform"
    
    print(f"\n🧪 TESTING: Running agent with input: {test_input}")
    print("="*60)
    
    try:
        result = await Runner.run(test_agent, f"Please save this: {test_input}")
        
        print("="*60)
        print("🧪 TESTING: Agent execution completed!")
        print(f"🧪 TESTING: Final output: {result.final_output}")
        
        return True
        
    except Exception as e:
        print(f"🧪 TESTING: Failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 MEMORY FUNCTION TOOL TEST")
    print("="*60)
    print("This tests if @function_tool approach triggers planner→actor workflow")
    print("Look for the debug logs from memory_manager.py:")
    print("- '🎯 Starting memory workflow...'") 
    print("- '🧠 Creating execution plan...'")
    print("- '⚡ Executing plan...'")
    print("="*60)
    
    success = asyncio.run(main())
    
    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED: Function tool approach works!")
        print("✅ Ready to apply to main chat agent")
    else:
        print("❌ TEST FAILED: Function tool approach has issues")
        print("❌ Need to debug before applying to main system")
    print("="*60) 