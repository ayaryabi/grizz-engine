"""
Simple Test Agent for Search Tool
Run this to test search functionality in terminal
"""
import asyncio
import logging
import sys
from agents import Agent, Runner
from app.tools.search_tools import search_web

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("SearchAgent")

class SimpleSearchAgent:
    """Simple agent that can search the web"""
    
    def __init__(self):
        logger.info("🤖 Initializing Search Agent...")
        
        # Create agent with search tool
        self.agent = Agent(
            name="Search Assistant",
            model="gpt-4o-mini",  # Cheap and fast for testing
            instructions="""
            You are a helpful search assistant. When users ask questions:
            
            1. If they need current information, facts, or research - use search_web tool
            2. Choose search mode based on complexity:
               - "fast" for simple facts, news, quick info
               - "deep" for analysis, comparisons, complex topics
            3. Always provide the search results to the user
            4. Be conversational and helpful
            
            Examples:
            - "What's the weather?" → search_web("current weather", "fast")
            - "Compare React vs Vue" → search_web("React vs Vue comparison", "deep")
            """,
            tools=[search_web]
        )
        logger.info("✅ Agent initialized with search tool")
    
    async def chat(self, user_input: str) -> str:
        """Process user input and return response"""
        logger.info(f"📝 User asked: {user_input}")
        
        try:
            # Agent processes the input and decides whether to use search
            logger.info("🔄 Agent thinking...")
            
            response = await Runner.run(self.agent, user_input)
            
            logger.info("✅ Agent response ready")
            return response.final_output
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return f"Sorry, I encountered an error: {e}"

async def main():
    """Main terminal interface"""
    print("\n" + "="*50)
    print("🔍 GRIZZ SEARCH AGENT TEST")
    print("="*50)
    print("Ask me anything! I'll search the web for current info.")
    print("Type 'quit' to exit")
    print("-"*50)
    
    # Initialize agent
    agent = SimpleSearchAgent()
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Process with agent
            print("\n🤖 Agent: ", end="", flush=True)
            response = await agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Check if required env vars are set
    import os
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("❌ PERPLEXITY_API_KEY not set!")
        print("Set it with: export PERPLEXITY_API_KEY=your_key_here")
        sys.exit(1)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set!")
        print("Set it with: export OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    print("✅ API keys found, starting agent...")
    asyncio.run(main()) 