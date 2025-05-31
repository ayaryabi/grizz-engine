from agents import Agent, Runner, trace
from .actor_agent import memory_actor_agent
from ...models.agents import MemoryPlan
from typing import Dict, Any
import traceback
import random
import time

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
    
    PLANNING STRATEGY:
    1. Analyze user intent from conversation context
    2. Determine what processing is needed:
       - If contains YouTube URL → use youtube_transcript with video_url parameter
       - If "summarize conversation" → use summarize_content first
       - If raw content → format and categorize in parallel
       - If user specifies category → respect user preference in categorization
    3. Create optimal execution plan with parallel steps where possible
    
    YOUTUBE URL DETECTION:
    If the user message contains YouTube URLs (youtube.com, youtu.be), extract the URL and use youtube_transcript action:
    - Extract the clean video URL from the message
    - Pass it as JSON string parameters: '{"video_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
    - Make other steps depend on youtube_transcript to process the transcript content
    
    CRITICAL PARALLELIZATION RULES:
    - format_markdown and categorize MUST run in PARALLEL with NO dependencies between them
    - Both format_markdown and categorize should process the original content independently
    - summarize_content (if needed) must happen BEFORE other steps
    - save_memory must wait for ALL processing steps to complete
    - youtube_transcript should run FIRST and other steps should depend on it
    - NEVER make categorize depend on format_markdown - they are independent!
    
    DEPENDENCY EXAMPLES:
    ✅ CORRECT (YouTube workflow):
    - Step 1: youtube_transcript (dependencies: [], parameters: '{"video_url": "https://www.youtube.com/watch?v=..."}')
    - Step 2: format_markdown (dependencies: ["step1"]) 
    - Step 3: categorize (dependencies: ["step1"])
    - Step 4: save_memory (dependencies: ["step2", "step3"])
    
    ✅ CORRECT (Regular content - Parallel):
    - Step 1: format_markdown (dependencies: [])
    - Step 2: categorize (dependencies: []) 
    - Step 3: save_memory (dependencies: ["step1", "step2"])
    
    ❌ WRONG (Sequential):
    - Step 1: format_markdown (dependencies: [])
    - Step 2: categorize (dependencies: ["step1"])  ← BAD!
    - Step 3: save_memory (dependencies: ["step2"])
    
    LEAN PLAN FORMAT:
    Generate MINIMAL plans with only essential fields:
    - plan_id: UNIQUE identifier using format: plan_{timestamp}_{random} (e.g., "plan_1704123456_a1b2c3d4")
    - steps: Array with step_id, action, dependencies, parameters (JSON string for youtube_transcript only)
    - estimated_time: Rough estimate in seconds
    - summary: Brief description
    
    IMPORTANT: Always generate truly unique plan_id values to avoid Redis collisions!
    Use current timestamp + random suffix: plan_{current_unix_timestamp}_{random_8_chars}
    
    DO NOT include:
    - parameters for actions other than youtube_transcript
    - tool_name (determined by action type)
    - description (keep plans lean)
    - user_request (already stored in Redis hash)
    
    AVAILABLE ACTIONS:
    - youtube_transcript: Extract transcript from YouTube videos (requires video_url parameter)
    - summarize_content: For conversation summaries
    - format_markdown: Clean formatting
    - categorize: Auto-categorize content
    - save_memory: Store to database
    
    Always consider the conversation context to understand user intent better.
    """,
    output_type=MemoryPlan,  # ← PLANNING ONLY - returns lean MemoryPlan
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
        user_id: str = None,  # Add user_id parameter
        **kwargs  # Accept any additional params but ignore them
    ) -> Dict[str, Any]:
        """
        Process a memory request through the unified agent workflow
        
        Args:
            user_request: The original user message with full intent and content
            user_id: User ID for database operations
            
        Returns:
            Dict with success status and result details
        """
        
        try:
            print(f"🎯 Starting memory workflow...")
            print(f"   📝 Request: {user_request}")
            print(f"   👤 User ID: {user_id}")
            
            # STEP 1: Let Memory Agent analyze the original message directly
            print(f"\n🧠 Creating execution plan...")
            
            # Just pass the original user message - let the Memory Agent be smart!
            plan_result = await Runner.run(self.agent, user_request)
            execution_plan = plan_result.final_output
            
            # CRITICAL FIX: Override plan_id to ensure uniqueness and prevent Redis collisions
            unique_plan_id = f"plan_{int(time.time())}_{random.randint(1000, 9999):04d}"
            execution_plan.plan_id = unique_plan_id
            
            print(f"📋 Plan created: {execution_plan.plan_id}")
            print(f"📝 Steps: {len(execution_plan.steps)}")
            
            # STEP 2: Save plan to Redis hash instead of massive string transfer
            print(f"\n⚡ Saving plan to Redis hash...")
            from .redis_orchestrator import redis_orchestrator
            
            # Pass user_id to Redis orchestrator
            plan_hash_key = await redis_orchestrator.save_plan_to_redis_hash(
                execution_plan, 
                user_request,
                user_id=user_id  # Add user_id parameter
            )
            
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
                "category": execution_data.category,
                "workflow_id": plan_hash_key  # Add workflow_id for output inspection
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