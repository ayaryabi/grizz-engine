from agents import Agent
from .memory_manager import MemoryManager
from typing import Dict, Any

class MasterMemoryAgent(Agent):
    """
    Memory Agent that exposes the existing planner→actor memory workflow as an agent.
    Can be used as agent.as_tool() for other agents.
    """
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        
        super().__init__(
            name="Memory Agent",
            instructions="""You are a specialized memory agent that saves and organizes information.

Your role:
1. Take user content and save it to memory with proper formatting
2. Use the existing memory management system (planner + actor workflow)
3. Categorize and tag content appropriately
4. Return clear status updates about what was saved

When users want to save content, process their request and save it using the memory system."""
        )
    
    async def run(self, user_input: str) -> str:
        """
        Process memory requests from user input
        """
        try:
            # Parse the user request to extract content and title
            # For now, treat the entire input as content
            result = await self.memory_manager.process_memory_request(
                user_request=user_input,
                content=user_input,
                title="User Content",
                item_type="note"
            )
            
            # Return a clear summary for the calling agent
            if result.get('success'):
                return f"""✅ Memory operation completed successfully!

**Content saved:** {result.get('title', 'User Content')}
**Memory ID:** {result.get('id', 'Generated')}
**Status:** Content has been formatted, categorized, and saved to memory

The content is now available for future retrieval and reference."""
            else:
                return f"❌ Memory operation failed: {result.get('error', 'Unknown error occurred')}"
                
        except Exception as e:
            return f"❌ Memory operation error: {str(e)}"

# Create singleton instance
master_memory_agent = MasterMemoryAgent() 