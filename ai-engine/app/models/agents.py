from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class PlanStep(BaseModel):
    """Individual step in a memory plan - lean version without redundant parameters"""
    step_id: str = Field(description="Unique step identifier")
    action: Literal["summarize_content", "format_markdown", "categorize", "save_memory"] = Field(
        description="Exact action type - must be one of these"
    )
    dependencies: List[str] = Field(default_factory=list, description="Step IDs that must complete first")

class MemoryPlan(BaseModel):
    """Structured plan from planner agent - lean version without redundant content"""
    plan_id: str = Field(description="Unique plan identifier")
    steps: List[PlanStep] = Field(description="Ordered list of steps to execute")
    estimated_time: int = Field(description="Estimated time in seconds")
    summary: str = Field(description="High-level summary of what will be done")

class MemoryExecutionResult(BaseModel):
    """Structured result from actor agent execution"""
    success: bool = Field(description="Whether the execution was successful")
    memory_id: str = Field(description="Database ID of the saved memory item")
    title: str = Field(description="Title of the saved content")
    category: str = Field(description="Category assigned to the content")
    summary: str = Field(description="Human readable summary of what was accomplished") 