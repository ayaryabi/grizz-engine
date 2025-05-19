from app.db.models import Message
from sqlalchemy.orm import Session

def fetch_recent_messages(conversation_id: str, db: Session, limit: int = 10):
    """
    Fetch the last N messages for a conversation, ordered chronologically.
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return messages[::-1]  # Return in chronological order 