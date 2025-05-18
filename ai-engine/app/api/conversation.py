from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date, func
from datetime import datetime, date
import pytz
from app.db.database import get_db
from app.db.models import Conversation
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
    # No need to validate user exists since we're using auth.users.id
    # which is guaranteed to exist if the user is authenticated
    
    # Get the current date in user's timezone
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        today_date = now.date()
    except pytz.exceptions.UnknownTimeZoneError:
        # Default to UTC if timezone is invalid
        now = datetime.now(pytz.UTC)
        today_date = now.date()
    
    # Convert today_date to datetime with time set to 00:00:00
    today_start = datetime.combine(today_date, datetime.min.time())
    today_start = tz.localize(today_start) if 'tz' in locals() else pytz.UTC.localize(today_start)
    
    # Convert to UTC for database storage
    today_start_utc = today_start.astimezone(pytz.UTC)
    
    # Look for existing conversation for today
    # We need to filter by date now since created_at will be in UTC
    conversation = db.query(Conversation)\
        .filter(Conversation.user_id == user_id)\
        .filter(Conversation.date == today_start_utc)\
        .first()
    
    # If no conversation exists for today, create one
    if not conversation:
        conversation = Conversation(
            user_id=user_id,
            title=f"Conversation on {today_date.strftime('%Y-%m-%d')}",
            date=today_start_utc,
            timezone=timezone
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "date": conversation.date
    }