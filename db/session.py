from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URLs
DB_FILE = "sqlite:///./Event_Manager_Database.db"

# Create engines for each database
engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})

# Create session makers for each database
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SessionLocal_usr = sessionmaker(autocommit=False, autoflush=False, bind=engine_usr)


# Get session
def get_db_session():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

# # Session getter for user database
# def get_user_session():
#     db = SessionLocal_usr()
#     try:
#         yield db
#     finally:
#         db.close()

# # Session getter for event database
# def get_event_session():
#     db = SessionLocal_usr()
#     try:
#         yield db
#     finally:
#         db.close()