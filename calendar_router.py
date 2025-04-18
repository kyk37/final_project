from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.event_model import Events
from db.session import get_event_session

calendar_router = APIRouter(prefix="/api", tags=["calendar"])

@calendar_router.get("/events")
def get_events(db: Session = Depends(get_event_session)):
    db_events = db.query(Events).all()
    return [
        {
            "title": event.title,
            "start": event.start_time.isoformat(),
            "end": event.end_time.isoformat()
        }
        for event in db_events
    ]
