from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.event_model import Events, Base

DATABASE_URL = "sqlite:///./event_database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

sample_events = [
    Events(
        title="Intro to Python",
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        location="Room 101",
        type="Class",
        description="CS class for beginners"
    ),
    Events(
        title="Group Project Meeting",
        start_time=datetime.now() + timedelta(days=1, hours=2),
        end_time=datetime.now() + timedelta(days=1, hours=4),
        location="Library B12",
        type="Meeting",
        description="Team sync for final project"
    ),
    Events(
        title="Yoga Session",
        start_time=datetime.now() + timedelta(days=2, hours=1),
        end_time=datetime.now() + timedelta(days=2, hours=2),
        location="Wellness Center",
        type="Event",
        description="Relax and recharge"
    )
]


def seed():
    db = SessionLocal()
    for event in sample_events:
        db.add(event)
    db.commit()
    db.close()
    print("Sample events added!")

if __name__ == "__main__":
    seed()