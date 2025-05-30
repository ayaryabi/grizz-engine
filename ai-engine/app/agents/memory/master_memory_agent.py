from agents import function_tool, RunContextWrapper
from .memory_manager import MemoryManager
from typing import Any

# Create memory manager instance
memory_manager = MemoryManager()

@function_tool
async def save_memory_content(
    wrapper: RunContextWrapper[Any]
) -> str:
    """Save and organize information into memory with proper categorization and formatting. Use this when users want to save content, notes, ideas, or information for later retrieval."""
    try:
        # Access the original user message from context wrapper
        original_message = wrapper.context.original_user_message
        
        # Use the Redis-optimized memory workflow with original message
        result = await memory_manager.process_memory_request(
            user_request=original_message  # Full context from user message
        )
        
        # Return minimal response - Chat Agent doesn't need details
        if result.get('success'):
            memory_id = result.get('id', 'unknown')
            category = result.get('category', 'general')
            return f"✅ Content saved to memory! (ID: {memory_id[:8]}, Category: {category})"
        else:
            return f"❌ Failed to save content: {result.get('error', 'Unknown error')}"
                
    except Exception as e:
        return f"❌ Memory error: {str(e)}" 