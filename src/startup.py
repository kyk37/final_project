from sqlalchemy.orm import Session
import bcrypt
from src.usr_model import User
from src.event_model import Events
from datetime import datetime, timedelta

def create_admin_user(db: Session):
    # Check bcrypt version for debugging
    try:
        print("bcrypt version:", bcrypt.__version__)
    except AttributeError:
        print("⚠️ bcrypt is broken — reinstall with pip!")
        return

    admin_username = "admin"
    admin_email = "admin@admin.com"
    admin_password = "admin"

    # Check if admin already exists
    existing_user = db.query(User).filter(User.username == admin_username).first()
    if existing_user:
        print("Admin user already exists, skipping creation.")
        return existing_user.uid  # Return the ID for potential use

    # Hash the admin password with bcrypt
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is a good default
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt)

    # Create and add new admin user
    admin_user = User(
        username=admin_username,
        email=admin_email,
        password_hashed=hashed_password,  # Store as bytes; adjust if your model expects a string
        first_name="Admin",
        last_name="User",
        is_organizer=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)  # Refresh to get the assigned ID
    print("Organizer (admin) user created with ID:", admin_user.id)
    return admin_user.uid  # Return ID for use in event creation

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
