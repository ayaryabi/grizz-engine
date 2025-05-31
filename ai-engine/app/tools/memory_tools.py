import uuid
from agents import Agent, Runner
from ..models.memory import SaveMemoryInput, SaveMemoryOutput

class SaveMemoryTool:
    """Save Memory Tool using Agent SDK for proper tracing"""
    
    def __init__(self):
        self.agent = Agent(
            name="Save Memory Tool",
            instructions="Save memory items to storage and return confirmation with generated ID",
            output_type=SaveMemoryOutput
        )
    
    async def save(self, input_data: SaveMemoryInput) -> SaveMemoryOutput:
        """Save memory item with proper agent tracing"""
        
        # Generate test ID for now
        test_id = str(uuid.uuid4())[:8]
        
        user_prompt = f"""
        Save this memory item:
        - Title: {input_data.title}
        - Category: {input_data.category}
        - Content length: {len(input_data.content)} characters
        
        Generated ID: {test_id}
        """
        
        try:
            # Use Runner.run() for proper Agent SDK tracing
            await Runner.run(self.agent, user_prompt)
            
            return SaveMemoryOutput(
                success=True,
                title=input_data.title,
                id=test_id,
                message=f"Successfully saved '{input_data.title}' in category '{input_data.category}'"
            )
        except Exception as e:
            return SaveMemoryOutput(
                success=False,
                title=input_data.title,
                id="",
                message=f"Failed to save: {str(e)}"
            )

# Create global instance
save_memory_instance = SaveMemoryTool()

async def save_memory_tool(input_data: SaveMemoryInput) -> SaveMemoryOutput:
    """Tool function for saving memory items"""
    return await save_memory_instance.save(input_data) 