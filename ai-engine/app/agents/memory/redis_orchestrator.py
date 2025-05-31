import asyncio
import json
import time
from typing import Dict, Any, List
from ...models.agents import MemoryPlan, PlanStep
from ...tools.markdown_tools import markdown_formatter_tool
from ...tools.categorization_tools import categorization_tool
from ...tools.memory_tools import save_memory_tool
from ...tools.summarization_tools import summarization_tool
from ...tools.youtube_tools import youtube_transcript_tool
from ...models.tools import MarkdownFormatInput, CategorizationInput, SummarizationInput, YouTubeTranscriptInput
from ...models.memory import SaveMemoryInput
from ...core.redis_client import get_redis_pool

class RedisWorkflowOrchestrator:
    """
    Redis-based workflow orchestrator - replaces massive string bottleneck
    Each tool reads from Redis hash, processes, writes back to Redis hash
    Eliminates Agent SDK string transfer overhead
    """
    
    def __init__(self):
        self.redis_conn = None
    
    async def _get_redis(self):
        """Get Redis connection"""
        if self.redis_conn is None:
            self.redis_conn = await get_redis_pool()
        return self.redis_conn
    
    async def save_plan_to_redis_hash(self, execution_plan: MemoryPlan, user_request: str) -> str:
        """Save plan and content to Redis hash, return hash key"""
        redis_conn = await self._get_redis()
        
        workflow_id = f"workflow:{execution_plan.plan_id}"
        
        # Save all data to Redis hash (Redis doesn't accept None values)
        workflow_data = {
            "plan_id": execution_plan.plan_id,
            "original_content": user_request,  # From context wrapper, not plan
            "plan_json": json.dumps(execution_plan.dict()),
            "status": "ready",
            "current_step": "",
            "completed_steps": json.dumps([]),
            "timing": json.dumps({}),
            
            # Step results (will be populated during execution) - empty strings instead of None
            "formatted_content": "",
            "summary": "",
            "category": "",
            "category_properties": "",
            "memory_id": "",
            "final_title": ""
        }
        
        await redis_conn.hset(workflow_id, mapping=workflow_data)
        print(f"💾 Saved lean workflow plan to Redis hash: {workflow_id}")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> str:
        """Execute complete workflow from Redis hash with parallel execution"""
        redis_conn = await self._get_redis()
        
        print(f"🚀 Starting Redis Workflow Orchestrator (Parallel)")
        print(f"📋 Workflow ID: {workflow_id}")
        print("=" * 80)
        
        overall_start = time.time()
        
        try:
            # Load plan from Redis
            workflow_data = await redis_conn.hgetall(workflow_id)
            plan_data = json.loads(workflow_data["plan_json"])
            plan = MemoryPlan(**plan_data)
            
            await redis_conn.hset(workflow_id, "status", "executing")
            
            print(f"📋 Plan loaded: {len(plan.steps)} steps")
            
            # Execute steps with dependency resolution and parallelization
            completed_steps = set()
            round_number = 1
            
            while len(completed_steps) < len(plan.steps):
                # Get steps ready for execution
                ready_steps = []
                for step in plan.steps:
                    if step.step_id not in completed_steps:
                        if all(dep_id in completed_steps for dep_id in step.dependencies):
                            ready_steps.append(step)
                
                if not ready_steps:
                    raise ValueError("Circular dependency or missing steps detected")
                
                print(f"\n🔄 Round {round_number}: Found {len(ready_steps)} ready steps")
                
                # Execute ready steps - PARALLEL when possible!
                if len(ready_steps) == 1:
                    # Single step - execute normally
                    step = ready_steps[0]
                    print(f"🔧 Executing: {step.step_id} ({step.action})")
                    step_start = time.time()
                    await self._execute_step(workflow_id, step)
                    step_duration = time.time() - step_start
                    completed_steps.add(step.step_id)
                    print(f"✅ Completed {step.step_id} in {step_duration:.2f}s")
                    
                else:
                    # Multiple independent steps - PARALLEL EXECUTION!
                    print(f"⚡ Executing {len(ready_steps)} steps in PARALLEL:")
                    for step in ready_steps:
                        print(f"   🔧 {step.step_id} ({step.action})")
                    
                    # Create parallel tasks
                    parallel_start = time.time()
                    tasks = [self._execute_step(workflow_id, step) for step in ready_steps]
                    
                    # Execute all steps concurrently
                    await asyncio.gather(*tasks)
                    parallel_duration = time.time() - parallel_start
                    
                    # Mark all as completed
                    for step in ready_steps:
                        completed_steps.add(step.step_id)
                    
                    print(f"⚡ All {len(ready_steps)} parallel steps completed in {parallel_duration:.2f}s")
                    print(f"💡 Parallel efficiency: {len(ready_steps)} steps in the time of 1!")
                
                round_number += 1
            
            # Mark as completed
            overall_time = time.time() - overall_start
            await redis_conn.hset(workflow_id, mapping={
                "status": "completed",
                "total_time": str(overall_time)
            })
            
            print("\n" + "=" * 80)
            print("🎉 PARALLEL WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"⏱️  Total Time: {overall_time:.2f} seconds")
            print(f"🚀 Executed in {round_number - 1} parallel rounds")
            
            # Get final results
            final_data = await redis_conn.hgetall(workflow_id)
            memory_id = final_data.get("memory_id", "unknown")
            category = final_data.get("category", "general")
            
            return f"Parallel workflow completed successfully. Memory ID: {memory_id}, Category: {category}"
            
        except Exception as e:
            await redis_conn.hset(workflow_id, mapping={
                "status": "failed",
                "error": str(e)
            })
            print(f"💥 PARALLEL WORKFLOW FAILED: {str(e)}")
            raise
    
    async def _execute_step(self, workflow_id: str, step: PlanStep):
        """Execute individual workflow step with enhanced parallel logging"""
        redis_conn = await self._get_redis()
        
        print(f"🔧 Starting Step: {step.step_id} ({step.action})")
        step_start = time.time()
        
        # Update current step tracking
        await redis_conn.hset(workflow_id, "current_step", step.step_id)
        
        try:
            if step.action == "format_markdown":
                # Load fresh data for this step
                workflow_data = await redis_conn.hgetall(workflow_id)
                await self._step_format_content(workflow_id, workflow_data)
            elif step.action == "summarize_content":
                # Load fresh data for this step
                workflow_data = await redis_conn.hgetall(workflow_id)
                await self._step_summarize_content(workflow_id, workflow_data)
            elif step.action == "categorize":
                # Load fresh data for this step
                workflow_data = await redis_conn.hgetall(workflow_id)
                await self._step_categorize_content(workflow_id, workflow_data)
            elif step.action == "save_memory":
                # Load fresh data for this step (includes updates from previous steps!)
                workflow_data = await redis_conn.hgetall(workflow_id)
                await self._step_save_content(workflow_id, workflow_data)
            elif step.action == "youtube_transcript":
                # Load fresh data for this step
                workflow_data = await redis_conn.hgetall(workflow_id)
                await self._step_youtube_transcript(workflow_id, workflow_data)
            else:
                raise ValueError(f"Unknown action: {step.action}")
            
            step_duration = time.time() - step_start
            print(f"✅ Completed {step.step_id} in {step_duration:.2f}s")
            
        except Exception as e:
            step_duration = time.time() - step_start
            print(f"❌ Failed {step.step_id} after {step_duration:.2f}s: {str(e)}")
            raise
        finally:
            # Clear current step
            await redis_conn.hset(workflow_id, "current_step", "none")
    
    async def _step_format_content(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Step 1: Format content using markdown formatter tool"""
        redis_conn = await self._get_redis()
        
        # Use transcript if available (YouTube workflow), otherwise use original content
        transcript_data = workflow_data.get("transcript")
        if transcript_data:
            content = transcript_data
            print(f"   📺 Using YouTube transcript ({len(content)} chars) for formatting")
        else:
            content = workflow_data["original_content"]
            print(f"   📝 Using original content ({len(content)} chars) for formatting")
        
        # Use existing tool
        input_data = MarkdownFormatInput(
            content=content,
            item_type="general"
        )
        result = await markdown_formatter_tool(input_data)
        
        # Update Redis hash
        await redis_conn.hset(workflow_id, mapping={
            "formatted_content": result.formatted_content,
            "formatted_length": str(len(result.formatted_content))
        })
        
        print(f"   📝 Formatted to {len(result.formatted_content)} chars")
    
    async def _step_summarize_content(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Step 2: Summarize formatted content"""
        redis_conn = await self._get_redis()
        
        formatted_content = workflow_data.get("formatted_content") or workflow_data["original_content"]
        
        # Use existing tool
        input_data = SummarizationInput(
            content=formatted_content,
            conversation_context="",
            summary_type="general"
        )
        result = await summarization_tool(input_data)
        
        # Update Redis hash
        await redis_conn.hset(workflow_id, mapping={
            "summary": result.summarized_content,
            "summary_length": str(len(result.summarized_content))
        })
        
        print(f"   📄 Summary: {len(result.summarized_content)} chars")
    
    async def _step_categorize_content(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Step 3: Categorize content"""
        redis_conn = await self._get_redis()
        
        # Use transcript if available (YouTube workflow), otherwise use original content
        transcript_data = workflow_data.get("transcript")
        if transcript_data:
            content = transcript_data
            print(f"   📺 Using YouTube transcript ({len(content)} chars) for categorization")
        else:
            content = workflow_data["original_content"]
            print(f"   📝 Using original content ({len(content)} chars) for categorization")
        
        # Use existing tool
        input_data = CategorizationInput(
            content=content,
            item_type="general",
            existing_categories=[],
            conversation_context="",
            user_intent=""
        )
        result = await categorization_tool(input_data)
        
        # Update Redis hash
        await redis_conn.hset(workflow_id, mapping={
            "category": result.category,
            "category_properties": json.dumps(result.properties)
        })
        
        print(f"   🏷️  Category: {result.category}")
    
    async def _step_save_content(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Step 4: Save content to memory database"""
        redis_conn = await self._get_redis()
        
        formatted_content = workflow_data.get("formatted_content") or workflow_data["original_content"]
        category = workflow_data.get("category", "general")
        original_content = workflow_data["original_content"]
        
        # Generate title from original content
        title = original_content[:50] + "..." if len(original_content) > 50 else original_content
        
        # Parse category properties
        try:
            category_properties = json.loads(workflow_data.get("category_properties", "{}"))
        except (json.JSONDecodeError, TypeError):
            category_properties = {}
        
        # Use existing tool
        input_data = SaveMemoryInput(
            item_type="general",
            title=title,
            content=formatted_content,
            properties=category_properties,
            category=category
        )
        result = await save_memory_tool(input_data)
        
        # Update Redis hash
        await redis_conn.hset(workflow_id, mapping={
            "memory_id": result.id,
            "final_title": result.title,
            "save_result": f"Saved with ID: {result.id}"
        })
        
        print(f"   💾 Saved with ID: {result.id}")

    async def _step_youtube_transcript(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Step 5: Extract YouTube video transcript using parameter-based approach"""
        redis_conn = await self._get_redis()
        
        # Load the plan to get the step parameters
        plan_data = json.loads(workflow_data["plan_json"])
        plan = MemoryPlan(**plan_data)
        
        # Find the youtube_transcript step to get its parameters
        youtube_step = None
        for step in plan.steps:
            if step.action == "youtube_transcript":
                youtube_step = step
                break
        
        if not youtube_step:
            raise Exception("YouTube transcript step not found in plan")
        
        # Use video_url parameter if provided, otherwise fallback to parsing user message
        video_url = None
        if youtube_step.parameters:
            try:
                params = json.loads(youtube_step.parameters)
                video_url = params.get("video_url")
            except (json.JSONDecodeError, TypeError):
                pass  # Fall back to extracting from message
        
        if not video_url:
            # Fallback: extract from original content using the extractor
            original_content = workflow_data["original_content"]
            from ...tools.youtube_tools import YouTubeTranscriptExtractor
            extractor = YouTubeTranscriptExtractor()
            urls = extractor.find_youtube_urls(original_content)
            if not urls:
                raise Exception("No YouTube URL found in message or parameters")
            video_url = urls[0]
        
        # Use YouTube tool with clean video_url parameter
        input_data = YouTubeTranscriptInput(
            video_url=video_url,
            item_type="youtube_video"
        )
        result = await youtube_transcript_tool(input_data)
        
        if result.success:
            # Update Redis hash with transcript for other steps to use
            await redis_conn.hset(workflow_id, mapping={
                "transcript": result.transcript,  # Save transcript for other steps
                "transcript_length": str(len(result.transcript)),
                "video_title": result.video_title,
                "video_id": result.video_id
            })
            print(f"   📺 YouTube transcript: {len(result.transcript)} chars from video {result.video_id}")
        else:
            print(f"   ❌ YouTube failed: {result.error_message}")
            raise Exception(f"YouTube transcript extraction failed: {result.error_message}")

# Global instance
redis_orchestrator = RedisWorkflowOrchestrator() 