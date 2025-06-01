from app.db.models import Memory
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session_maker
import logging
from uuid import UUID
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def save_memory_to_database(
    user_id: str,
    title: str,
    content: str,
    category: str,
    item_type: str = "note"
) -> Dict[str, Any]:
    """
    Save a memory to the database and return result dict.
    
    Args:
        user_id: The user's UUID as string
        title: Memory title
        content: Memory content (markdown)
        category: Memory category for properties
        item_type: Type of memory item (default: "note")
        
    Returns:
        Dict: {
            "success": bool,
            "memory_id": str,
            "message": str
        }
    """
    try:
        async with async_session_maker() as db:
            # Create new memory record with minimal required fields
            memory = Memory(
                user_id=UUID(user_id),
                item_type=item_type,
                title=title,
                content=content,
                properties={"category": category}
                # Skip visibility and moderation_status to avoid enum issues
            )
            
            # Add to session and commit
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            logger.info(f"💾 Saved memory with ID: {memory.id} for user: {user_id}")
            
            return {
                "success": True,
                "memory_id": str(memory.id),
                "message": f"Memory '{title}' saved successfully"
            }
        
    except Exception as e:
        logger.error(f"Error saving memory to database: {str(e)}", exc_info=True)
        return {
            "success": False,
            "memory_id": "",
            "message": f"Failed to save memory: {str(e)}"
        } 