import uuid
from agents import Agent, Runner
from ..models.memory import SaveMemoryInput, SaveMemoryOutput
from ..services.memory_database_service import save_memory_to_database
import asyncio
import logging

logger = logging.getLogger(__name__)

class SaveMemoryTool:
    """Save Memory Tool using real database integration"""
    
    def __init__(self):
        self.agent = Agent(
            name="Save Memory Tool",
            instructions="Save memory items to storage and return confirmation with generated ID",
            output_type=SaveMemoryOutput
        )
    
    async def save(
        self, 
        input_data: SaveMemoryInput, 
        user_id: str,
        category: str = "general"
    ) -> SaveMemoryOutput:
        """Save memory item to real database"""
        
        try:
            logger.info(f"💾 Saving memory to database for user: {user_id}")
            
            # Call real database service
            result = await save_memory_to_database(
                user_id=user_id,
                title=input_data.title,
                content=input_data.content,
                category=category,
                item_type="note",
                properties=input_data.properties  # Pass the rich metadata!
            )
            
            if result["success"]:
                logger.info(f"✅ Memory saved successfully: {result['memory_id']}")
                
                # Still use Agent SDK for tracing
                user_prompt = f"""
                Memory saved successfully:
                - ID: {result['memory_id']}
                - Title: {input_data.title}
                - Category: {category}
                - User: {user_id}
                """
                
                try:
                    await Runner.run(self.agent, user_prompt)
                except Exception as trace_error:
                    logger.warning(f"Agent SDK tracing failed: {trace_error}")
                
                return SaveMemoryOutput(
                    success=True,
                    title=input_data.title,
                    id=result["memory_id"],
                    message=result["message"]
                )
            else:
                logger.error(f"❌ Database save failed: {result.get('error', 'Unknown error')}")
                
                return SaveMemoryOutput(
                    success=False,
                    title=input_data.title,
                    id="",
                    message=result.get("message", "Failed to save to database")
                )
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in save tool: {str(e)}")
            return SaveMemoryOutput(
                success=False,
                title=input_data.title,
                id="",
                message=f"Failed to save: {str(e)}"
            )

# Create global instance
save_memory_instance = SaveMemoryTool()

async def save_memory_tool(
    input_data: SaveMemoryInput, 
    user_id: str, 
    category: str = "general"
) -> SaveMemoryOutput:
    """Tool function for saving memory items with user_id"""
    return await save_memory_instance.save(input_data, user_id, category) 