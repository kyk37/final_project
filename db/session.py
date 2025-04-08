from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.usr_model import User
from src.event_model import Events

USER_DATABASE_URL = "sqlite:///./user_database.db"
EVENT_DATABASE_URL = "sqlite:///./event_database.db"

engine_usr = create_engine(USER_DATABASE_URL, connect_args={"check_same_thread": False})
engine_event = create_engine(EVENT_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False)
SessionLocal.configure(binds={User: engine_usr, Events: engine_event})

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
