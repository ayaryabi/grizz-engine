import uuid
from ..models.memory import SaveMemoryInput, SaveMemoryOutput

async def save_memory_tool(input_data: SaveMemoryInput) -> SaveMemoryOutput:
    """
    Save memory item to storage (testing mode - no database yet)
    
    For now just generates a test ID and returns title + id as specified.
    Later will integrate with actual database.
    """
    
    # Generate test ID for now
    test_id = str(uuid.uuid4())[:8]
    
    # Simulate successful save
    return SaveMemoryOutput(
        success=True,
        title=input_data.title,
        id=test_id,
        message=f"Successfully saved '{input_data.title}' in category '{input_data.category}'"
    ) 