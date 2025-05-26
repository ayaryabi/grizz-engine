from agents import Agent, Runner
from .planner_agent import memory_planner_agent
from .actor_agent import memory_actor_agent
from typing import Dict, Any
import traceback

# Main Memory Agent using direct agent handoffs (no decorator needed)
memory_agent = Agent(
    name="Memory Agent",
    instructions="""
    You coordinate memory operations by delegating to specialists. You will receive a request with:
    - User request (what they want to do)
    - Content type (e.g., youtube_video, meeting, note)
    - Content (the actual content to save)  
    - Title (title for the content)
    
    Your workflow:
    1. Hand off to the Memory Actor agent to execute the memory workflow and save content
    
    The Agent SDK automatically passes the full conversation context during handoffs.
    After the handoff completes, provide a summary of the results to the user.
    """,
    handoffs=[memory_actor_agent],
    model="gpt-4o"
)

class MemoryManager:
    """Simple wrapper for the unified memory agent"""
    
    def __init__(self):
        # Just store the agent reference
        self.agent = memory_agent
    
    async def process_memory_request(
        self, 
        user_request: str, 
        content: str, 
        title: str = "Untitled",
        item_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Process a memory request through the unified agent workflow
        
        Args:
            user_request: What the user wants to do
            content: The content to save
            title: Title for the content
            item_type: Type of content (youtube_video, meeting, etc.)
            
        Returns:
            Dict with success status and result details
        """
        
        try:
            print(f"🎯 Starting memory workflow...")
            print(f"   📝 Request: {user_request}")
            print(f"   📄 Content length: {len(content)} chars")
            print(f"   🏷️  Type: {item_type}")
            
            # Single Agent SDK call with handoffs for unified tracing
            print(f"\n🧠 Creating execution plan...")
            workflow_input = f"""
            User request: {user_request}
            Content type: {item_type}
            Content: {content}
            Title: {title}
            
            Please coordinate the memory workflow using handoffs to planner and actor agents.
            """
            
            result = await Runner.run(self.agent, workflow_input)
            execution_result = result.final_output
            
            print(f"✅ Execution completed!")
            
            # Parse the execution result to extract title and ID
            parsed_result = {
                "success": True,
                "execution_log": execution_result,
                "title": title,
                "id": None
            }
            
            # Try to extract ID from the result string
            if "🆔 ID:" in execution_result:
                lines = execution_result.split('\n')
                for line in lines:
                    if "🆔 ID:" in line:
                        parsed_result["id"] = line.split("🆔 ID:")[-1].strip()
                        break
            
            # Try to extract title from result if available
            if "📝 Title:" in execution_result:
                lines = execution_result.split('\n')
                for line in lines:
                    if "📝 Title:" in line:
                        parsed_result["title"] = line.split("📝 Title:")[-1].strip()
                        break
            
            return parsed_result
            
        except Exception as e:
            print(f"❌ Memory workflow failed with error: {str(e)}")
            print(f"📍 Error type: {type(e).__name__}")
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "title": title,
                "id": None
            } 