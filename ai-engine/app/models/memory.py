from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class MemoryItem(BaseModel):
    """Basic memory item for testing (no database yet)"""
    item_type: str = Field(description="Type of content: youtube_video, meeting_transcript, article, note, etc.")
    title: str = Field(min_length=1, max_length=200, description="Title of the memory item")
    content: str = Field(min_length=1, description="The actual content to save")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Searchable properties like date, person, etc.")

class SaveMemoryInput(BaseModel):
    """Input for save_memory tool"""
    item_type: str = Field(description="Type of content being saved")
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    properties: Dict[str, Any] = Field(default_factory=dict)
    category: str = Field(description="Category assigned by categorization tool")

class SaveMemoryOutput(BaseModel):
    """Output from save_memory tool - just title and id for now"""
    success: bool
    title: str
    id: str = Field(description="Generated memory ID for testing")
    message: str = Field(description="Confirmation message") 