from app.db.models import Message
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def fetch_recent_messages(conversation_id: str, db: Session, limit: int = 10):
    """
    Fetch the last N messages for a conversation, ordered chronologically.
    Uses direct SQL for improved performance over ORM.
    """
    try:
        # Direct SQL query for better performance
        result = db.execute(
            text("""
                SELECT id, conversation_id, user_id, role, content, created_at 
                FROM messages 
                WHERE conversation_id = :conv_id
                ORDER BY created_at DESC 
                LIMIT :limit
            """),
            {"conv_id": conversation_id, "limit": limit}
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
            for row in result
        ]
        
        # Return in chronological order
        return messages[::-1]
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        # Return empty list to avoid breaking the chat flow
        return [] 