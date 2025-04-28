from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.usr_model import User
from src.event_model import Events

'''
    Not sure if this is used of not... I think it might be.. but it already exists in main()
'''
# Database URLs
USER_DATABASE_URL = "sqlite:///./user_database.db"

# Create engines for each database
engine_usr = create_engine(USER_DATABASE_URL, connect_args={"check_same_thread": False})

# Create session makers for each database
SessionLocal_usr = sessionmaker(autocommit=False, autoflush=False, bind=engine_usr)

# Session getter for user database
def get_user_session():
    db = SessionLocal_usr()
    try:
        yield db
    finally:
        db.close()

# Session getter for event database
def get_event_session():
    db = SessionLocal_usr()
    try:
        yield db
    finally:
        db.close()