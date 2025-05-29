from agents import function_tool, RunContextWrapper
from .memory_manager import MemoryManager
from typing import Any

# Create memory manager instance
memory_manager = MemoryManager()

@function_tool
async def save_memory_content(
    wrapper: RunContextWrapper[Any],
    content: str = ""  # Fixed: no leading underscore
) -> str:
    """Save and organize information into memory with proper categorization and formatting. Use this when users want to save content, notes, ideas, or information for later retrieval."""
    try:
        # Access the original user message from context
        original_message = wrapper.context.original_user_message
        
        # Use the full planner→actor memory workflow with original message
        result = await memory_manager.process_memory_request(
            user_request=original_message  # Just the original message - that's all we need!
        )
        
        # Format the response from the planner→actor workflow
        if result.get('success'):
            return f"""**Memory Saved Successfully!**

- **Category**: {result.get('category', 'General')}
- **Content**: {result.get('title', 'Content')}
- **Memory ID**: {result.get('id', 'No ID')}
- **Tags**: {', '.join(result.get('tags', []))}

Status: {result.get('execution_summary', 'Memory saved successfully.')}"""
        else:
            return f"❌ Memory operation failed: {result.get('error', 'Unknown error occurred')}"
                
    except Exception as e:
        return f"❌ Memory operation error: {str(e)}" 