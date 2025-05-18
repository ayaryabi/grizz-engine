from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, time
import pytz

from app.db.database import get_db
from app.db.models import Conversation

router = APIRouter()

@router.get("/conversations/today")
async def get_or_create_today_conversation(
    user_id: str,                           # temp until real auth dep
    tz: str = Query("UTC", description="IANA timezone, e.g. Europe/Berlin"),
    db: Session = Depends(get_db),
):
    # 1) Resolve timezone safely
    try:
        zone = pytz.timezone(tz)
    except pytz.UnknownTimeZoneError:
        zone = pytz.UTC  # fallback

    print(f"Received tz: {tz}")
    print(f"Zone: {zone}")

    # 2) Compute user's local date (calendar day)
    today_local = datetime.now(zone).date()  # User's local date (e.g., 2025-05-19)
    print(f"today_local: {today_local}")
    print(f"Querying for user_id={user_id}, conv_day={today_local}")

    # 3) Lookup or create using local date
    convo = (
        db.query(Conversation)
        .filter_by(user_id=user_id, conv_day=today_local)
        .first()
    )

    if convo:
        print(f"Found conversation: {convo.id}, conv_day={convo.conv_day}")
    else:
        print("No conversation found, creating new one.")

    if convo is None:
        convo = Conversation(
            user_id=user_id,
            title=f"Conversation on {today_local.isoformat()}",
            conv_day=today_local,
            user_tz=zone.zone,
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)

    return {
        "id":        convo.id,
        "title":     convo.title,
        "conv_day":  convo.conv_day,      # Local DATE, e.g. 2025-05-19
        "user_tz":   convo.user_tz,
    }