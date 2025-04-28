from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URLs
DB_FILE = "sqlite:///./Event_Manager_Database.db"

# Create engines for each database
engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})

# Create session makers for each database
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Get session
def get_db_session():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
