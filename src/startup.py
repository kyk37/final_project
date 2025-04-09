from sqlalchemy.orm import Session
import bcrypt
from src.usr_model import User
from src.event_model import Events
from datetime import datetime, timedelta

def create_admin_user(db: Session):
    # Define user credentials
    admin_username = "admin"
    admin_email = "admin@admin.com"
    admin_password = "admin"

    test_username = "test"
    test_email = "test@test.com"
    test_password = "test"

    # Check if admin user exists
    existing_admin = db.query(User).filter(User.username == admin_username).first()
    if existing_admin:
        admin_user = existing_admin
    else:
        # Create admin user with its own salt
        salt_admin = bcrypt.gensalt(rounds=12)
        hashed_admin_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt_admin)
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hashed=hashed_admin_password,
            first_name="Admin",
            last_name="User",
            is_organizer=True
        )
        db.add(admin_user)

    # Check if test user exists
    existing_test = db.query(User).filter(User.username == test_username).first()
    if not existing_test:
        # Create test user with its own salt
        salt_test = bcrypt.gensalt(rounds=12)
        hashed_test_password = bcrypt.hashpw(test_password.encode('utf-8'), salt_test)
        test_user = User(
            username=test_username,  # Fixed typo from original (was test_user)
            email=test_email,
            password_hashed=hashed_test_password,
            first_name="Test",
            last_name="User",
            is_organizer=False
        )
        db.add(test_user)

    # Commit all changes to the database
    db.commit()

    # Log and return the admin user's UID
    print("Organizer (admin) user with ID:", admin_user.uid)
    return admin_user.uid


def create_events(db: Session, organizer_uid):
    sample_events = [
        Events(
            owner_uid=organizer_uid,
            title="Intro to Python",
            date=datetime.now(),
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            location="Room 101",
            type="Class",
            description="CS class for beginners"
        ),
        Events(
            owner_uid=organizer_uid,
            title="Group Project Meeting",
            date=datetime.now(),
            start_time=datetime.now() + timedelta(days=1, hours=2),
            end_time=datetime.now() + timedelta(days=1, hours=4),
            location="Library B12",
            type="Meeting",
            description="Team sync for final project"
        ),
        Events(
            owner_uid=organizer_uid,
            title="Yoga Session",
            date=datetime.now(),
            start_time=datetime.now() + timedelta(days=2, hours=1),
            end_time=datetime.now() + timedelta(days=2, hours=2),
            location="Wellness Center",
            type="Event",
            description="Relax and recharge"
        )
    ]
    for event in sample_events:
        db.add(event)
    db.commit()
    print("Sample events added!")
