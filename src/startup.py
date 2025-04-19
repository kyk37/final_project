from sqlalchemy.orm import Session
import bcrypt
from src.usr_model import User
from src.event_model import Events
from datetime import datetime, timedelta, date
from src.usr_model import User

def create_admin_user(db: Session):
    # Define user credentials
    admin_username = "admin"
    admin_email = "admin@admin.com"
    admin_password = "admin"

    test_username = "test"
    test_email = "test@test.com"
    test_password = "test"

    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == admin_username).first()
    if not admin_user:
        # Create admin user with its own salt
        salt_admin = bcrypt.gensalt(rounds=12)
        hashed_admin_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt_admin)
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hashed=hashed_admin_password,
            first_name="admin_first_name",
            last_name="admin_last_name",
            created_at=datetime.now(),
            is_organizer=True,
            profile_image_url="/static/defaults/default_avatar.jpg"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Created admin user with ID: {admin_user.uid}")

    # Check if test user exists
    test_user = db.query(User).filter(User.username == test_username).first()
    if not test_user:
        # Create test user with its own salt
        salt_test = bcrypt.gensalt(rounds=12)
        hashed_test_password = bcrypt.hashpw(test_password.encode('utf-8'), salt_test)
        test_user = User(
            username=test_username,
            email=test_email,
            password_hashed=hashed_test_password,
            first_name="Test",
            last_name="User",
            created_at=datetime.now(),
            is_organizer=False,
            profile_image_url="/static/defaults/default_avatar.jpg"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Created test user with ID: {test_user.uid}")

    return admin_user

def create_events(event_db: Session, user_db: Session, organizer_uid: int):
    from datetime import datetime, timedelta

    organizer_in_user_db = user_db.query(User).filter_by(uid=organizer_uid).first()
    if not organizer_in_user_db:
        print("Organizer not found in user DB!")
        return

    # Merge organizer into event DB session
    organizer = event_db.merge(organizer_in_user_db)

    now = datetime.now()
    sample_events = [
        Events(
            owner_uid=organizer.uid,
            title="Intro to Python",
            date=now.date(),
            start_time=now,
            end_time=now + timedelta(hours=1),
            location="Room 101",
            event_type="Class",
            organizer="CS Department",
            tags="tech, beginner, python",
            image_urls="/static/img/python_poster.png",
            description="CS class for beginners"
        ),
        Events(
            owner_uid=organizer.uid,
            title="Group Project Meeting",
            date=now.date(),
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=4),
            location="Library B12",
            event_type="Meeting",
            organizer="Project Team",
            tags="project, team, collaboration",
            image_urls="/static/img/project_meeting.png",
            description="Team sync for final project"
        ),
        Events(
            owner_uid=organizer.uid,
            title="Yoga Session",
            date=now.date(),
            start_time=now + timedelta(days=2, hours=1),
            end_time=now + timedelta(days=2, hours=2),
            location="Wellness Center",
            event_type="Gym Class",
            organizer="Student Wellness Club",
            tags="health, wellness, yoga",
            image_urls="/static/img/yoga_class.jpg",
            description="Relax and recharge"
        )
    ]

    for event in sample_events:
        event.attendees.append(organizer)  # Add the organizer as an attendee
        event_db.add(event)

    event_db.commit()