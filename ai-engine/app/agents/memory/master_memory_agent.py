from agents import function_tool, trace
from .memory_manager import MemoryManager
from typing import Dict, Any

class MemoryToolWrapper:
    """
    Simple wrapper that exposes the existing planner→actor memory workflow as a tool.
    No new agents - just wraps the existing MemoryManager.
    """
    
    def __init__(self):
        # Just use the existing memory manager (which has planner + actor)
        self.memory_manager = MemoryManager()
    
    async def process_memory_request(
        self, 
        user_request: str, 
        content: str, 
        title: str = "Untitled",
        item_type: str = "note"
    ) -> Dict[str, Any]:
        """
        Process a memory request using the full planner→actor workflow
        """
        # Let the MemoryManager handle its own tracing - don't add extra trace wrapper
        result = await self.memory_manager.process_memory_request(
            user_request=user_request,
            content=content,
            title=title,
            item_type=item_type
        )
        return result
    
    def as_tool(self, tool_name: str = None, tool_description: str = None):
        """
        Expose the existing planner→actor memory workflow as a tool
        """
        
        @function_tool(
            name_override=tool_name or "save_memory_content",
            description_override=tool_description or """
            Save and process content to memory with intelligent planning and execution.
            
            This tool handles the complete memory workflow:
            - Creates structured execution plans
            - Formats content appropriately 
            - Categorizes and tags content
            - Saves to memory database
            
            Use this when users want to save information, content, or notes.
            """
        )
        async def memory_tool(
            user_request: str,
            content: str, 
            title: str = "Untitled",
            content_type: str = "note"
        ) -> str:
            """
            Save and process content to memory
            
            Args:
                user_request: What the user wants to do (e.g., "Save this content", "Remember this for later")
                content: The actual content to save
                title: Title for the content
                content_type: Type of content (note, meeting, youtube_video, etc.)
            """
            try:
                result = await self.process_memory_request(
                    user_request=user_request,
                    content=content,
                    title=title,
                    item_type=content_type
                )
                
                # Return a clear summary for the calling agent
                if result.get('success'):
                    return f"""✅ Memory operation completed successfully!

**What was saved:** {title}
**Content type:** {content_type}
**Memory ID:** {result.get('id', 'Generated')}
**Status:** Content has been formatted, categorized, and saved to memory

The content is now available for future retrieval and reference."""
                else:
                    return f"❌ Memory operation failed: {result.get('error', 'Unknown error occurred')}"
                    
            except Exception as e:
                return f"❌ Memory operation error: {str(e)}"
        
        return memory_tool

# Create singleton instance
memory_tool_wrapper = MemoryToolWrapper() 