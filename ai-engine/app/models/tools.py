from pydantic import BaseModel, Field
from typing import Dict, Any, List

class MarkdownFormatInput(BaseModel):
    """Input for markdown formatting tool"""
    content: str = Field(min_length=1, description="Raw content to format")
    item_type: str = Field(description="Type of content for context")

class MarkdownFormatOutput(BaseModel):
    """Output from markdown formatting tool"""
    formatted_content: str = Field(description="Nicely formatted markdown")
    success: bool = Field(description="Whether formatting was successful")

class CategorizationInput(BaseModel):
    """Input for categorization tool"""
    content: str = Field(min_length=1, description="Content to categorize")
    item_type: str = Field(description="Type of content (youtube_video, meeting, etc.)")
    existing_categories: List[str] = Field(default_factory=list, description="List of existing categories")
    conversation_context: str = Field(default="", description="Previous conversation context")
    user_intent: str = Field(default="", description="User's stated intent or category preference")

class CategorizationOutput(BaseModel):
    """Output from categorization tool"""
    category: str = Field(description="Chosen or created category")
    is_new_category: bool = Field(description="Whether this is a new category")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in categorization")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Extracted searchable properties")

class SummarizationInput(BaseModel):
    """Input for summarization tool"""
    content: str = Field(description="Content to summarize")
    conversation_context: str = Field(default="", description="Previous conversation context")
    summary_type: str = Field(default="general", description="Type of summary: conversation, content, project")

class SummarizationOutput(BaseModel):
    """Output from summarization tool"""
    summarized_content: str = Field(description="The summarized content in markdown format")
    success: bool = Field(description="Whether summarization was successful") 