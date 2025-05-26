from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class PlanStep(BaseModel):
    """Individual step in a memory plan"""
    step_id: str = Field(description="Unique step identifier")
    action: Literal["format_markdown", "categorize", "save_memory"] = Field(
        description="Exact action type - must be one of these"
    )
    tool_name: str = Field(description="Exact tool function name to call")
    parameters: Dict[str, Any] = Field(description="Parameters to pass to the tool")
    dependencies: List[str] = Field(default_factory=list, description="Step IDs that must complete first")
    description: str = Field(description="Human readable description of this step")

class MemoryPlan(BaseModel):
    """Structured plan from planner agent"""
    plan_id: str = Field(description="Unique plan identifier")
    user_request: str = Field(description="Original user request")
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute")
    estimated_time: int = Field(description="Estimated time in seconds")
    summary: str = Field(description="High-level summary of what will be done") 