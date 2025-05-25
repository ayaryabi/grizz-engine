import asyncio
from app.agents.chat_agent import chat_agent

async def test_agent_sdk():
    print("🧪 Testing Agent SDK integration...")
    
    try:
        result = await chat_agent.process("Hello, this is a test message!")
        print(f"✅ Agent SDK works! Response: {result[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Agent SDK test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent_sdk())
    if success:
        print("🎉 All tests passed! Agent SDK integration is working.")
    else:
        print("💥 Tests failed. Need to debug Agent SDK integration.") 