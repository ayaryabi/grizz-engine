from app.db.models import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import logging

logger = logging.getLogger(__name__)

async def fetch_recent_messages(conversation_id: str, db: AsyncSession, limit: int = 10):
    """
    Fetch the last N messages for a conversation, ordered chronologically.
    Uses SQLAlchemy Core for improved performance over ORM with async support.
    """
    try:
        # Async SQL execution with SQLAlchemy Core
        result = await db.execute(
            select(Message.id, Message.conversation_id, Message.user_id, 
                   Message.role, Message.content, Message.created_at)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        # Convert to list of dict
        messages = [
            {
                "id": row.id,
                "conversation_id": row.conversation_id,
                "user_id": row.user_id,
                "role": row.role,
                "content": row.content,
                "created_at": row.created_at
            }
            for row in result.all()
        ]
        
        # Return in chronological order
        return messages[::-1]
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        # Return empty list to avoid breaking the chat flow
        return [] 