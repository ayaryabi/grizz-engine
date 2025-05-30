from agents import Agent, Runner, trace
from .actor_agent import memory_actor_agent
from ...models.agents import MemoryPlan
from typing import Dict, Any
import traceback

# Main Memory Agent using direct agent handoffs (no decorator needed)
memory_agent = Agent(
    name="Memory Agent",
    instructions="""
    You are a memory planning coordinator that helps users save different types of content based on conversation context.
    
    IMPORTANT: When users reference "G", "Grizz", or "greece", they are talking to the assistant. Take these references seriously and understand what the user wants - this indicates direct communication with the AI assistant and their intent should be carefully analyzed.
    
    CONTENT TYPES YOU HANDLE:
    - Images: User shares images for projects, reference, etc.
    - YouTube transcripts: From channels, educational videos, etc.  
    - Project information: Work docs, ideas, plans
    - Conversation summaries: "Summarize our discussion about X and save it"
    - Meeting notes: Transcripts, action items
    - Articles/Documents: Research, reference materials
    
    AVAILABLE TOOLS:
    - summarize_content_tool: Summarize conversations or long content
    - format_content_tool: Clean formatting into markdown
    - categorize_content_tool: Auto-categorize and tag content with context awareness
    - save_content_tool: Store to database
    
    PLANNING STRATEGY:
    1. Analyze user intent from conversation context
    2. Determine what processing is needed:
       - If "summarize conversation" → use summarize_content_tool first
       - If raw content → format and categorize in parallel
       - If user specifies category → respect user preference in categorization
    3. Create optimal execution plan with parallel steps where possible
    
    PARALLELIZATION RULES:
    - Summarization must happen BEFORE formatting/categorization
    - Formatting and categorization can run in PARALLEL
    - Saving must wait for all processing to complete
    
    Always consider the conversation context to understand user intent better.
    Include conversation context and user intent in tool parameters where needed.
    """,
    output_type=MemoryPlan,  # ← PLANNING ONLY - returns MemoryPlan
    model="gpt-4.1-mini-2025-04-14"
)

class MemoryManager:
    """Simple wrapper for the unified memory agent"""
    
    def __init__(self):
        # Just store the agent reference
        self.agent = memory_agent
    
    async def process_memory_request(
        self, 
        user_request: str, 
        **kwargs  # Accept any additional params but ignore them
    ) -> Dict[str, Any]:
        """
        Process a memory request through the unified agent workflow
        
        Args:
            user_request: The original user message with full intent and content
            
        Returns:
            Dict with success status and result details
        """
        
        try:
            print(f"🎯 Starting memory workflow...")
            print(f"   📝 Request: {user_request}")
            
            # STEP 1: Let Memory Agent analyze the original message directly
            print(f"\n🧠 Creating execution plan...")
            
            # Just pass the original user message - let the Memory Agent be smart!
            plan_result = await Runner.run(self.agent, user_request)
            execution_plan = plan_result.final_output
            
            print(f"📋 Plan created: {execution_plan.plan_id}")
            print(f"📝 Steps: {len(execution_plan.steps)}")
            
            # STEP 2: Save plan to Redis hash instead of massive string transfer
            print(f"\n⚡ Saving plan to Redis hash...")
            from .redis_orchestrator import redis_orchestrator
            
            plan_hash_key = await redis_orchestrator.save_plan_to_redis_hash(execution_plan, user_request)
            
            # STEP 3: Execute via Redis orchestrator (eliminates bottleneck)
            print(f"\n⚡ Executing plan via Redis...")
            execution_input = f"Execute workflow from Redis hash: {plan_hash_key}"
            
            execution_result = await Runner.run(memory_actor_agent, execution_input)
            execution_data = execution_result.final_output  # This is now MemoryExecutionResult!
            
            print(f"✅ Execution completed!")
            print(f"🆔 Memory ID: {execution_data.memory_id}")
            
            # Return structured result
            return {
                "success": execution_data.success,
                "plan": execution_plan.dict(),
                "execution_summary": execution_data.summary,
                "title": execution_data.title,
                "id": execution_data.memory_id,
                "category": execution_data.category
            }
            
        except Exception as e:
            print(f"❌ Memory workflow failed with error: {str(e)}")
            print(f"📍 Error type: {type(e).__name__}")
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "title": "Error",
                "id": None
            } 