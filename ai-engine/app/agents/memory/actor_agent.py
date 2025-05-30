from agents import Agent, function_tool
from ...models.tools import MarkdownFormatInput, CategorizationInput, SummarizationInput
from ...models.memory import SaveMemoryInput
from ...models.agents import MemoryPlan, PlanStep, MemoryExecutionResult
from ...tools.markdown_tools import markdown_formatter_tool
from ...tools.categorization_tools import categorization_tool
from ...tools.memory_tools import save_memory_tool
from ...tools.summarization_tools import summarization_tool
from typing import Dict, Any, List
from pydantic import BaseModel
import asyncio
import json

# Simple function tools that only use basic types
@function_tool
async def summarize_content_tool(
    content: str, 
    conversation_context: str = "", 
    summary_type: str = "general"
) -> str:
    """Summarize content with optional conversation context"""
    input_data = SummarizationInput(
        content=content,
        conversation_context=conversation_context,
        summary_type=summary_type
    )
    result = await summarization_tool(input_data)
    return result.summarized_content

@function_tool
async def format_content_tool(content: str, item_type: str = "unknown") -> str:
    """Format content into clean markdown"""
    input_data = MarkdownFormatInput(content=content, item_type=item_type)
    result = await markdown_formatter_tool(input_data)
    return result.formatted_content

@function_tool  
async def categorize_content_tool(
    content: str, 
    conversation_context: str = "", 
    user_intent: str = "", 
    item_type: str = "unknown"
) -> str:
    """Categorize content and extract properties with context awareness, returns 'category|properties_json'"""
    input_data = CategorizationInput(
        content=content, 
        item_type=item_type,
        existing_categories=[],
        conversation_context=conversation_context,
        user_intent=user_intent
    )
    result = await categorization_tool(input_data)
    # Return as simple string to avoid schema issues
    import json
    try:
        props_json = json.dumps(result.properties)
    except (TypeError, ValueError) as e:
        # Fallback for properties that can't be serialized
        props_json = json.dumps({"error": "Properties serialization failed", "details": str(e)})
    return f"{result.category}|{props_json}"

@function_tool
async def save_content_tool(title: str, content: str, category: str, item_type: str = "unknown") -> str:
    """Save content to memory database, returns 'title|id'"""
    input_data = SaveMemoryInput(
        item_type=item_type,
        title=title,
        content=content,
        properties={},  # Simple empty dict
        category=category
    )
    result = await save_memory_tool(input_data)
    return f"{result.title}|{result.id}"

@function_tool
async def save_memory_database_tool(
    title: str, 
    content: str, 
    category: str, 
    item_type: str = "unknown",
    properties: str = "{}"
) -> str:
    """Direct access to save_memory_tool from memory_tools.py - saves to database and returns JSON result"""
    try:
        import json
        properties_dict = json.loads(properties) if properties else {}
    except:
        properties_dict = {}
    
    input_data = SaveMemoryInput(
        item_type=item_type,
        title=title,
        content=content,
        properties=properties_dict,
        category=category
    )
    result = await save_memory_tool(input_data)
    
    return json.dumps({
        "success": result.success,
        "title": result.title,
        "id": result.id,
        "message": result.message
    })

@function_tool
async def execute_memory_plan(plan_json: str, content: str, title: str, item_type: str = "unknown") -> str:
    """Execute a structured memory plan with dependency resolution and parallelization"""
    
    try:
        # Parse the plan
        plan_data = json.loads(plan_json)
        plan = MemoryPlan(**plan_data)
        
        print(f"🎯 Executing Memory Plan: {plan.summary}")
        print(f"📋 Total steps: {len(plan.steps)}")
        
        # Track step results and completion
        step_results = {}
        completed_steps = set()
        
        # Build dependency graph
        def get_ready_steps() -> List[PlanStep]:
            """Get steps that have all dependencies completed"""
            ready = []
            for step in plan.steps:
                if step.step_id not in completed_steps:
                    if all(dep_id in completed_steps for dep_id in step.dependencies):
                        ready.append(step)
            return ready
        
        # Execute step function
        async def execute_step(step: PlanStep) -> str:
            """Execute a single plan step"""
            print(f"🔧 Executing Step {step.step_id}: {step.description}")
            
            if step.action == "format_markdown":
                result = await format_content_tool(content, item_type)
                step_results[step.step_id] = result
                return result
                
            elif step.action == "categorize":
                # Use formatted content if available, otherwise original
                content_to_use = step_results.get("format_step", content)
                result = await categorize_content_tool(content_to_use, "", "", item_type)
                step_results[step.step_id] = result
                return result
                
            elif step.action == "save_memory":
                # Get required data from previous steps
                formatted_content = step_results.get("format_step", content)
                category_result = step_results.get("categorize_step", "general|{}")
                category = category_result.split("|")[0]
                
                result = await save_content_tool(title, formatted_content, category, item_type)
                step_results[step.step_id] = result
                return result
            
            else:
                raise ValueError(f"Unknown action: {step.action}")
        
        # Execute plan with dependency resolution
        while len(completed_steps) < len(plan.steps):
            ready_steps = get_ready_steps()
            
            if not ready_steps:
                raise ValueError("Circular dependency or missing steps detected")
            
            # Group steps that can run in parallel (no dependencies between them)
            parallel_groups = []
            remaining_steps = ready_steps[:]
            
            while remaining_steps:
                # Start a new parallel group
                current_group = [remaining_steps.pop(0)]
                
                # Add more steps to this group if they don't depend on each other
                i = 0
                while i < len(remaining_steps):
                    step = remaining_steps[i]
                    # Check if this step can run with current group
                    can_parallel = True
                    for group_step in current_group:
                        if (step.step_id in group_step.dependencies or 
                            group_step.step_id in step.dependencies):
                            can_parallel = False
                            break
                    
                    if can_parallel:
                        current_group.append(remaining_steps.pop(i))
                    else:
                        i += 1
                
                parallel_groups.append(current_group)
            
            # Execute parallel groups sequentially, but steps within groups in parallel
            for group in parallel_groups:
                if len(group) == 1:
                    # Single step
                    step = group[0]
                    await execute_step(step)
                    completed_steps.add(step.step_id)
                    print(f"✅ Completed: {step.step_id}")
                else:
                    # Multiple steps in parallel
                    print(f"⚡ Running {len(group)} steps in parallel...")
                    tasks = [execute_step(step) for step in group]
                    await asyncio.gather(*tasks)
                    
                    for step in group:
                        completed_steps.add(step.step_id)
                        print(f"✅ Completed: {step.step_id}")
        
        # Return final result
        final_result = step_results.get("save_step", "No save step found")
        print(f"🎉 Plan execution completed! Final result: {final_result}")
        
        return f"Plan executed successfully. {final_result}"
        
    except Exception as e:
        error_msg = f"Plan execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

@function_tool
async def execute_workflow_from_redis(workflow_id: str) -> str:
    """Execute workflow from Redis hash - eliminates massive string bottleneck"""
    try:
        from .redis_orchestrator import redis_orchestrator
        result = await redis_orchestrator.execute_workflow(workflow_id)
        return result
    except Exception as e:
        error_msg = f"Redis workflow execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg

# Pure Agent SDK agent for memory execution
memory_actor_agent = Agent(
    name="Memory Actor Agent", 
    instructions="""
    You are a memory execution agent. Your job is simple: execute the plan you receive.
    
    EXECUTION PATTERN:
    1. If you receive a Redis workflow ID (format: "Execute workflow from Redis hash: workflow:..."), use execute_workflow_from_redis tool
    2. If you receive a structured plan, use the traditional execute_memory_plan tool
    3. Return structured results with the actual database ID
    
    TOOL USAGE:
    - execute_workflow_from_redis: For Redis hash-based workflows (preferred - faster)
    - execute_memory_plan: For legacy structured plan execution
    - save_memory_database_tool: Direct access to core database saving tool (always available)
    - save_content_tool: Wrapper tool for simple saving
    - Other tools: Use as needed for individual steps
    
    IMPORTANT: When save_content_tool returns "title|id", extract the ID and include it in your structured response.
    The save tool returns data like "My Title|abc123" - extract "abc123" as the memory_id.
    
    Be efficient, accurate, and always return the actual memory ID from saving.
    Always execute steps in dependency order and return the structured result.
    """,
    output_type=MemoryExecutionResult,  # ← Structured output!
    model="gpt-4.1-mini-2025-04-14",  # Fast execution model
    tools=[summarize_content_tool, format_content_tool, categorize_content_tool, save_content_tool, save_memory_database_tool, execute_memory_plan, execute_workflow_from_redis]
) 