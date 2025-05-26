from agents import Agent, function_tool
from ...models.tools import MarkdownFormatInput, CategorizationInput
from ...models.memory import SaveMemoryInput
from ...tools.markdown_tools import markdown_formatter_tool
from ...tools.categorization_tools import categorization_tool
from ...tools.memory_tools import save_memory_tool
from typing import Dict, Any
from pydantic import BaseModel

# Simple function tools that only use basic types
@function_tool
async def format_content_tool(content: str, item_type: str = "unknown") -> str:
    """Format content into clean markdown"""
    input_data = MarkdownFormatInput(content=content, item_type=item_type)
    result = await markdown_formatter_tool(input_data)
    return result.formatted_content

@function_tool  
async def categorize_content_tool(content: str, item_type: str = "unknown") -> str:
    """Categorize content and extract properties, returns 'category|properties_json'"""
    input_data = CategorizationInput(
        content=content, 
        item_type=item_type,
        existing_categories=[]
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

# Pure Agent SDK agent for memory execution
memory_actor_agent = Agent(
    name="Memory Actor Agent", 
    instructions="""
    You are a memory actor agent that executes memory operations step by step.
    
    Available tools:
    1. format_content_tool(content, item_type) - Format content as markdown, returns formatted string
    2. categorize_content_tool(content, item_type) - Categorize content, returns "category|properties_json"
    3. save_content_tool(title, content, category, item_type) - Save to database, returns "title|id"
    
    Follow this workflow:
    1. Format the content using format_content_tool
    2. Categorize the formatted content using categorize_content_tool  
    3. Save the content using save_content_tool
    
    Always execute steps in order and use the output from previous steps as input to the next.
    Return the final title and ID from the save operation.
    """,
    model="gpt-4o-mini",  # Fast execution model
    tools=[format_content_tool, categorize_content_tool, save_content_tool]
) 