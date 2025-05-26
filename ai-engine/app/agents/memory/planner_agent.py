import uuid
from ...agents.base_agent import BaseGrizzAgent
from ...models.agents import MemoryPlan, PlanStep
from typing import Dict, Any
import json

class MemoryPlannerAgent(BaseGrizzAgent):
    """Creates structured execution plans for memory operations"""
    
    def __init__(self):
        super().__init__(
            name="Memory Planner",
            instructions="""
            You are a memory operation planner. Your job is to create detailed execution plans for saving user content.
            
            Available tools and their exact names:
            1. "markdown_formatter_tool" - Format content into clean markdown
            2. "categorization_tool" - Categorize content and extract properties  
            3. "save_memory_tool" - Save the final formatted and categorized content
            
            IMPORTANT: You must create a plan with these EXACT steps in order:
            1. First: format_markdown (use markdown_formatter_tool)
            2. Second: categorize (use categorization_tool) 
            3. Third: save_memory (use save_memory_tool)
            
            Each step must depend on the previous one. Always follow this sequence.
            
            People might give you:
            - YouTube video transcripts
            - Meeting transcripts
            - Articles
            - Notes
            - Case studies
            - Any text content
            
            Your job is to plan the right tools to use for processing their content.
            
            Always return a structured JSON plan in this format:
            {
                "plan_id": "unique_id",
                "user_request": "original_request",
                "summary": "plan_summary",
                "estimated_time": 30,
                "steps": [
                    {
                        "step_id": "step_1",
                        "action": "format_markdown",
                        "tool_name": "markdown_formatter_tool",
                        "parameters": {"content": "content", "item_type": "type"},
                        "dependencies": [],
                        "description": "Format content as markdown"
                    }
                ]
            }
            """,
            llm_type="planning"
            # Removed output_type to avoid strict JSON schema issues
        )
    
    async def create_plan(self, user_request: str, item_type: str = "unknown") -> MemoryPlan:
        """Create a structured plan for memory operations"""
        
        user_prompt = f"""
        Create a plan for this request:
        User request: {user_request}
        Content type: {item_type}
        
        Return a structured plan with 3 steps: format_markdown, categorize, save_memory
        """
        
        try:
            # Use Agent SDK with structured output
            result = await self.process(user_prompt)
            
            # If Agent SDK returns a MemoryPlan object directly, use it
            if isinstance(result, MemoryPlan):
                return result
            
            # Otherwise, try to parse as JSON
            if isinstance(result, str):
                plan_data = json.loads(result)
                steps = [
                    PlanStep(
                        step_id=step["step_id"],
                        action=step["action"],
                        tool_name=step["tool_name"],
                        parameters=step["parameters"],
                        dependencies=step["dependencies"],
                        description=step["description"]
                    )
                    for step in plan_data["steps"]
                ]
                
                return MemoryPlan(
                    plan_id=plan_data["plan_id"],
                    user_request=plan_data["user_request"],
                    steps=steps,
                    estimated_time=plan_data["estimated_time"],
                    summary=plan_data["summary"]
                )
            
        except Exception as e:
            print(f"Planner failed with Agent SDK, using fallback: {e}")
            
        # Fallback plan if Agent SDK fails
        plan_id = str(uuid.uuid4())[:8]
        return MemoryPlan(
            plan_id=plan_id,
            user_request=user_request,
            summary="Simple fallback plan",
            estimated_time=30,
            steps=[
                PlanStep(
                    step_id="step_1",
                    action="format_markdown",
                    tool_name="markdown_formatter_tool",
                    parameters={"content": "content", "item_type": item_type},
                    dependencies=[],
                    description="Format content as markdown"
                ),
                PlanStep(
                    step_id="step_2", 
                    action="categorize",
                    tool_name="categorization_tool",
                    parameters={"content": "content", "item_type": item_type, "existing_categories": []},
                    dependencies=["step_1"],
                    description="Categorize content"
                ),
                PlanStep(
                    step_id="step_3",
                    action="save_memory",
                    tool_name="save_memory_tool", 
                    parameters={"title": "Untitled", "content": "content", "item_type": item_type, "category": "general", "properties": {}},
                    dependencies=["step_2"],
                    description="Save to memory"
                )
            ]
        ) 