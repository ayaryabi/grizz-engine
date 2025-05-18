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
        zone = pytz.UTC                                          # fallback

    # 2) Compute local midnight *today*, then convert to UTC DATE
    today_local = datetime.now(zone).date()                      # ← fixed
    naive_midnight = datetime.combine(today_local, time.min)     # 00:00
    local_midnight   = zone.localize(naive_midnight)
    conv_day_utc: date = local_midnight.astimezone(pytz.UTC).date()

    # 3) Lookup or create
    convo = (
        db.query(Conversation)
        .filter_by(user_id=user_id, conv_day=conv_day_utc)
        .first()
    )

    if convo is None:
        convo = Conversation(
            user_id=user_id,
            title=f"Conversation on {conv_day_utc.isoformat()}",
            conv_day=conv_day_utc,
            user_tz=zone.zone,
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)

    return {
        "id":        convo.id,
        "title":     convo.title,
        "conv_day":  convo.conv_day,      # UTC DATE, e.g. 2025-05-18
        "user_tz":   convo.user_tz,
    }