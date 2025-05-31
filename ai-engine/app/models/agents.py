from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union

class PlanStep(BaseModel):
    """Individual step in a memory plan - with optional parameters for specific actions"""
    step_id: str = Field(description="Unique step identifier")
    action: Literal["summarize_content", "format_markdown", "categorize", "save_memory", "youtube_transcript"] = Field(
        description="Exact action type - must be one of these"
    )
    dependencies: List[str] = Field(default_factory=list, description="Step IDs that must complete first")
    parameters: Optional[Union[str, None]] = Field(default=None, description="JSON string of action-specific parameters for youtube_transcript")

class MemoryPlan(BaseModel):
    """Structured plan from planner agent - lean version with optional parameters"""
    plan_id: str = Field(description="Unique plan identifier")
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute")
    estimated_time: int = Field(default=30, description="Estimated execution time in seconds")
    summary: str = Field(default="", description="Brief description of the plan")

class MemoryExecutionResult(BaseModel):
    """Structured result from actor agent execution"""
    success: bool = Field(description="Whether the execution was successful")
    memory_id: str = Field(description="Database ID of the saved memory item")
    title: str = Field(description="Title of the saved content")
    category: str = Field(description="Category assigned to the content")
    summary: str = Field(description="Human readable summary of what was accomplished") 