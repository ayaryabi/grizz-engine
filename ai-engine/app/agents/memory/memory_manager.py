from agents import Agent, Runner, trace
from .actor_agent import memory_actor_agent
from ...models.agents import MemoryPlan
from typing import Dict, Any
import traceback

# Main Memory Agent using direct agent handoffs (no decorator needed)
memory_agent = Agent(
    name="Memory Agent",
    instructions="""
    You are a memory planning coordinator. Analyze the user's memory request and create a structured execution plan.
    
    Available tools for execution:
    - format_content_tool: Format content as clean markdown
    - categorize_content_tool: Categorize content and extract properties
    - save_content_tool: Save formatted content to database
    
    Create an optimal execution plan considering:
    1. Dependencies: formatting must happen before categorization and saving
    2. Parallelization: some steps can run simultaneously to improve performance
    3. Tool parameters: specify exact parameters each tool needs
    
    Use these exact action types and tool names:
    - action: "format_markdown", tool_name: "format_content_tool"
    - action: "categorize", tool_name: "categorize_content_tool"  
    - action: "save_memory", tool_name: "save_content_tool"
    
    After creating the structured plan, hand off to Memory Actor for execution.
    """,
    output_type=MemoryPlan,  # ← RESTORED: We DO want structured planning
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
            
            # Let the test agent's tool call provide the main trace - no manual trace wrapper
            # STEP 1: Create structured plan using Memory Agent
            print(f"\n🧠 Creating execution plan...")
            plan_input = f"""
            User request: {user_request}
            Content type: {item_type}
            Content: {content}
            Title: {title}
            
            Create a structured execution plan for this memory operation.
            """
            
            plan_result = await Runner.run(self.agent, plan_input)
            execution_plan = plan_result.final_output
            
            print(f"📋 Plan created: {execution_plan.plan_id}")
            print(f"📝 Steps: {len(execution_plan.steps)}")
            
            # STEP 2: Execute plan using Memory Actor Agent  
            print(f"\n⚡ Executing plan...")
            execution_input = f"""
            Execute this memory plan:
            
            Plan ID: {execution_plan.plan_id}
            User Request: {execution_plan.user_request}
            Content: {content}
            Title: {title}
            Type: {item_type}
            
            Steps to execute:
            {chr(10).join([f"{i+1}. {step.action} - {step.description}" for i, step in enumerate(execution_plan.steps)])}
            
            Follow the steps in order and use the available tools.
            """
            
            execution_result = await Runner.run(memory_actor_agent, execution_input)
            execution_data = execution_result.final_output  # This is now MemoryExecutionResult!
            
            print(f"✅ Execution completed!")
            print(f"🆔 Memory ID: {execution_data.memory_id}")
            
            # Return structured result - no more text parsing needed!
            return {
                "success": execution_data.success,
                "plan": execution_plan.dict(),
                "execution_summary": execution_data.summary,
                "title": execution_data.title,
                "id": execution_data.memory_id,  # ← Direct access to ID!
                "category": execution_data.category
            }
            
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