from sqlalchemy.orm import Session
import bcrypt
from src.usr_model import User
from src.event_model import Events
from datetime import datetime, timedelta, date
from src.usr_model import User
import random

def create_startup_users(db: Session):
    organizer_map = {}
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
            admin= True,
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
            profile_image_url="/static/defaults/default_avatar.jpg",
            admin=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Created test user with ID: {test_user.uid}")


    # Organizer accounts
    organizers = ["CS Department", "Student Council", "Wellness Club", "Career Center", "AI Lab"]

    for org_name in organizers:
        username = org_name.lower().replace(" ", "_")
        email = f"{username}@events.com"
        password = "organizer"

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Organizer '{username}' already exists. Using existing account.")
            organizer_map[org_name] = existing
            continue

        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

        organizer = User(
            username=username,
            email=email,
            password_hashed=hashed_password,
            first_name=org_name.split()[0],
            last_name=org_name.split()[-1] if len(org_name.split()) > 1 else "Team",
            created_at=datetime.now(),
            is_organizer=True,
            admin=False,
            profile_image_url="/static/defaults/default_avatar.jpg"
        )
        db.add(organizer)
        db.commit()
        db.refresh(organizer) 
        organizer_map[org_name] = organizer.uid
        print(f" Created organizer '{username}' with ID: {organizer.uid}")


    return organizer_map

def random_datetime(start_range, end_range):
    total_seconds = int((end_range - start_range).total_seconds())
    random_offset = timedelta(seconds=random.randint(0, total_seconds))
    return start_range + random_offset


def create_events(event_db: Session, organizer_map: dict[str, int]):
    titles = [
        "Intro to Python", "Data Science Workshop", "AI Ethics Panel", "React Crash Course",
        "Cybersecurity 101", "Hackathon Planning", "Career Fair Prep", "Yoga Session",
        "Mindfulness Hour", "Resume Review", "Cloud Computing", "Group Project Meeting",
        "Blockchain Basics", "ML Model Tuning", "Internship Panel", "Final Exam Review",
        "Startup Pitch Night", "Robotics Demo", "VR Gaming Showcase", "Women in Tech",
        "Public Speaking", "Student Townhall", "SAT Prep", "Dance Workshop",
        "Meditation Break", "Campus Tour", "Finance 101", "Art Showcase", "Chess Tournament",
        "Language Exchange", "Alumni Mixer", "Creative Coding", "Film Screening",
        "Sustainability Forum", "Podcast Club", "E-sports Event", "Study Jam",
        "Toastmasters", "Mental Health Talk", "Community Cleanup"
    ]

    locations = ["Room 101", "Library B12", "Hall A", "Zoom", "Auditorium", "Wellness Center", "Café Lounge"]
    organizers = list(organizer_map.keys())
    types = ["Class", "Meeting", "Workshop", "Gym Class", "Event"]
    tags = ["tech, beginner", "health, wellness", "career, resume", "project, collaboration", "fun, social"]
    images = ["/static/img/python_poster.png", "/static/img/project_meeting.png", "/static/img/yoga_class.jpg"]

    now = datetime.now()
    start_range = now - timedelta(days=30)
    end_range = now + timedelta(days=90)

    def random_datetime(start, end):
        delta = end - start
        return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

    for i in range(100):
        start_time = random_datetime(start_range, end_range)
        end_time = start_time + timedelta(hours=random.randint(1, 3))
        title = titles[i % len(titles)]

        organizer_name = random.choice(organizers)
        organizer_uid = organizer_map.get(organizer_name)

        if not organizer_uid:
            print(f"Skipping event: Organizer '{organizer_name}' has no UID.")
            continue

        organizer_user = event_db.get(User, organizer_uid)
        if not organizer_user:
            print(f"Skipping event: Organizer UID {organizer_uid} not found in DB.")
            continue

        event = Events(
            owner_uid=organizer_user.uid,
            title=title,
            date=start_time.date(),
            start_time=start_time,
            end_time=end_time,
            location=random.choice(locations),
            event_type=random.choice(types),
            organizer=organizer_name,
            tags=random.choice(tags),
            image_urls=random.choice(images),
            description=f"This is a session on {title.lower()}",
            archived=start_time.date() < now.date()
        )

        event.attendees.append(organizer_user)
        event_db.add(event)

        event_db.commit()