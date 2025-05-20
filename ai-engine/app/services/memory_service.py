from app.db.models import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import logging

logger = logging.getLogger(__name__)

async def fetch_recent_messages(conversation_id: str, db: AsyncSession, limit: int = 10):
    """
    Fetch the last N messages for a conversation, ordered chronologically.
    Uses SQLAlchemy 2.0 style select for async support.
    """
    try:
        # Create a query to select entire Message objects
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        # Execute the query
        result = await db.execute(query)
        
        # Get all Message objects
        messages = result.scalars().all()
        
        # Return in chronological order (oldest first)
        messages_list = list(messages)
        messages_list.reverse()
        
        logger.info(f"Fetched {len(messages_list)} messages for conversation {conversation_id}")
        return messages_list
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}", exc_info=True)
        # Return empty list to avoid breaking the chat flow
        return [] 