import uuid
from agents import Runner
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
            3. "save_memory_tool" - Save formatted content to database
            
            You must create a plan with exactly 3 steps in this order:
            1. Step 1: Use "markdown_formatter_tool" with action "format_markdown"
            2. Step 2: Use "categorization_tool" with action "categorize" (depends on step 1)
            3. Step 3: Use "save_memory_tool" with action "save_memory" (depends on step 2)
            
            Return your plan in this exact JSON format:
            {
                "plan_id": "unique_id",
                "user_request": "original_user_request",
                "summary": "Format, categorize, and save user content",
                "estimated_time": 30,
                "steps": [
                    {
                        "step_id": "step_1",
                        "description": "Format content as clean markdown",
                        "tool_name": "markdown_formatter_tool",
                        "action": "format_markdown",
                        "parameters": {"item_type": "user_provided_type"},
                        "dependencies": []
                    },
                    {
                        "step_id": "step_2", 
                        "description": "Categorize content and extract properties",
                        "tool_name": "categorization_tool",
                        "action": "categorize",
                        "parameters": {"item_type": "user_provided_type"},
                        "dependencies": ["step_1"]
                    },
                    {
                        "step_id": "step_3",
                        "description": "Save content to memory database", 
                        "tool_name": "save_memory_tool",
                        "action": "save_memory",
                        "parameters": {"item_type": "user_provided_type"},
                        "dependencies": ["step_2"]
                    }
                ]
            }
            """,
            llm_type="planning"  # Use smart planning model
        )
    
    async def create_plan(self, user_request: str, item_type: str = "unknown") -> MemoryPlan:
        """Create a structured execution plan"""
        
        try:
            # Use Runner.run() to get proper Agent SDK tracing
            prompt = f"""
            Create an execution plan for this user request: "{user_request}"
            Content type: {item_type}
            
            Return only the JSON plan, no other text.
            """
            
            result = await Runner.run(self, prompt)
            plan_json = result.final_output
            
            # Parse and validate the plan
            plan_data = json.loads(plan_json)
            steps = [PlanStep(**step) for step in plan_data["steps"]]
            
            return MemoryPlan(
                plan_id=plan_data["plan_id"],
                user_request=plan_data["user_request"],
                summary=plan_data["summary"],
                estimated_time=plan_data["estimated_time"],
                steps=steps
            )
            
        except Exception as e:
            print(f"⚠️ Planner failed: {str(e)}, using fallback")
            # Fallback plan if AI fails - include ALL required fields
            fallback_id = str(uuid.uuid4())[:8]
            return MemoryPlan(
                plan_id=fallback_id,
                user_request=user_request,  # Add missing field
                summary="Simple fallback plan",
                estimated_time=30,  # Add missing field
                steps=[
                    PlanStep(
                        step_id="step_1",
                        description="Format content as markdown",
                        tool_name="markdown_formatter_tool",
                        action="format_markdown", 
                        parameters={"item_type": item_type},
                        dependencies=[]
                    ),
                    PlanStep(
                        step_id="step_2",
                        description="Categorize and extract properties",
                        tool_name="categorization_tool",
                        action="categorize",
                        parameters={"item_type": item_type},
                        dependencies=["step_1"]
                    ),
                    PlanStep(
                        step_id="step_3", 
                        description="Save to memory database",
                        tool_name="save_memory_tool",
                        action="save_memory",
                        parameters={"item_type": item_type},
                        dependencies=["step_2"]
                    )
                ]
            ) 