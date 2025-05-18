from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Conversation, Message

router = APIRouter()

@router.get("/db-test")
async def test_db_connection(db: Session = Depends(get_db)):
    """
    Simple endpoint to test database connectivity and table access.
    """
    try:
        # Test if we can query conversations table
        conversation_count = db.query(Conversation).count()
        
        # Test if we can query messages table
        message_count = db.query(Message).count()
        
        return {
            "status": "Database connection successful",
            "conversation_count": conversation_count,
            "message_count": message_count,
        }
    except Exception as e:
        return {
            "status": "Database connection failed",
            "error": str(e)
        } 