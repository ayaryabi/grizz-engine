from agents import Runner
from .planner_agent import MemoryPlannerAgent
from .actor_agent import MemoryActorAgent
from ..base_agent import BaseGrizzAgent
from typing import Dict, Any
import traceback

class MemoryManager(BaseGrizzAgent):
    """Coordinates the memory planner and actor agents"""
    
    def __init__(self):
        super().__init__(
            name="Memory Manager",
            instructions="Coordinate memory operations by managing planner and actor agents to save user content efficiently.",
            llm_type="execution"  # Coordination doesn't need heavy reasoning
        )
        self.planner = MemoryPlannerAgent()
        self.actor = MemoryActorAgent()
    
    async def process_memory_request(
        self, 
        user_request: str, 
        content: str, 
        title: str = "Untitled",
        item_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Process a memory request through the planner-actor workflow
        
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
            
            # Step 1: Create execution plan using the planner agent
            print(f"\n🧠 Creating execution plan...")
            plan = await self.planner.create_plan(user_request, item_type)
            
            print(f"✅ Plan created: {plan.summary}")
            print(f"📋 Plan ID: {plan.plan_id}")
            print(f"🔧 Steps: {len(plan.steps)}")
            
            # Step 2: Execute the plan using the actor agent
            print(f"\n⚡ Executing plan...")
            execution_result = await self.actor.execute_plan(
                plan=plan,
                original_content=content,
                original_title=title
            )
            
            print(f"✅ Execution completed!")
            
            # Parse the execution result to extract title and ID
            result = {
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
                        result["id"] = line.split("🆔 ID:")[-1].strip()
                        break
            
            # Try to extract title from result if available
            if "📝 Title:" in execution_result:
                lines = execution_result.split('\n')
                for line in lines:
                    if "📝 Title:" in line:
                        result["title"] = line.split("📝 Title:")[-1].strip()
                        break
            
            return result
            
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