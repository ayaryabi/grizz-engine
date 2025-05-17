from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date, func
from datetime import datetime, date
import pytz
from app.db.database import get_db
from app.db.models import User, Conversation
from typing import Optional

router = APIRouter()

@router.get("/conversations/today")
async def get_today_conversation(
    user_id: str,
    timezone: str = Query("UTC", description="User's IANA timezone string"),
    db: Session = Depends(get_db)
):
    """
    Gets or creates today's conversation for the user.
    Uses the user's timezone to determine what 'today' means.
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the current date in user's timezone
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        today_date = now.date()
    except pytz.exceptions.UnknownTimeZoneError:
        # Default to UTC if timezone is invalid
        now = datetime.now(pytz.UTC)
        today_date = now.date()
    
    # PostgreSQL-compatible date extraction from timestamp
    # Look for existing conversation for today
    conversation = db.query(Conversation)\
        .filter(Conversation.user_id == user_id)\
        .filter(cast(Conversation.created_at, Date) == today_date)\
        .first()
    
    # If no conversation exists for today, create one
    if not conversation:
        conversation = Conversation(
            user_id=user_id,
            title=f"Conversation on {today_date.strftime('%Y-%m-%d')}",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at
    }