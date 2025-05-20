from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, time
import pytz
from sqlalchemy import select
import logging

from app.db.database import get_async_db
from app.db.models import Conversation
from app.core.auth import get_current_user_id_from_token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/conversations/today")
async def get_or_create_today_conversation(
    tz: str = Query("UTC", description="IANA timezone, e.g. Europe/Berlin"),
    user_id: str = Depends(get_current_user_id_from_token),
    db: AsyncSession = Depends(get_async_db),
):
    # 1) Resolve timezone safely
    try:
        zone = pytz.timezone(tz)
    except pytz.UnknownTimeZoneError:
        zone = pytz.UTC  # fallback

    logger.info(f"Received tz: {tz}")
    logger.info(f"Zone: {zone}")

    # 2) Compute user's local date (calendar day)
    today_local = datetime.now(zone).date()  # User's local date (e.g., 2025-05-19)
    logger.info(f"today_local: {today_local}")
    logger.info(f"Querying for user_id={user_id}, conv_day={today_local}")

    # 3) Lookup or create using local date with async SQLAlchemy 2.0 style
    try:
        # Use proper select statement for async SQLAlchemy
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.conv_day == today_local
        )
        result = await db.execute(stmt)
        convo = result.scalar_one_or_none()

        if convo:
            logger.info(f"Found conversation: {convo.id}, conv_day={convo.conv_day}")
        else:
            logger.info("No conversation found, creating new one.")

        if convo is None:
            convo = Conversation(
                user_id=user_id,
                title=f"Conversation on {today_local.isoformat()}",
                conv_day=today_local,
                user_tz=zone.zone,
            )
            db.add(convo)
            await db.commit()
            await db.refresh(convo)

        return {
            "id":        str(convo.id),  # Convert UUID to string
            "title":     convo.title,
            "conv_day":  convo.conv_day.isoformat(),  # Format date as string
            "user_tz":   convo.user_tz,
        }
    except Exception as e:
        logger.error(f"Error in get_or_create_today_conversation: {str(e)}")
        # Roll back the transaction in case of error
        await db.rollback()
        raise