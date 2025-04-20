from sqlalchemy.orm import Session
import bcrypt
from src.usr_model import User
from src.event_model import Events
from datetime import datetime, timedelta, date
from src.usr_model import User
import random

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

def random_datetime(start_range, end_range):
    total_seconds = int((end_range - start_range).total_seconds())
    random_offset = timedelta(seconds=random.randint(0, total_seconds))
    return start_range + random_offset

def create_events(event_db: Session, user_db: Session, organizer_uid: int):
    from datetime import datetime, timedelta

    organizer_in_user_db = user_db.query(User).filter_by(uid=organizer_uid).first()
    if not organizer_in_user_db:
        print("Organizer not found in user DB!")
        return

    # Merge organizer into event DB session
    organizer = event_db.merge(organizer_in_user_db)


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
    organizers = ["CS Department", "Student Council", "Wellness Club", "Career Center", "AI Lab"]
    types = ["Class", "Meeting", "Workshop", "Gym Class", "Event"]
    tags = ["tech, beginner", "health, wellness", "career, resume", "project, collaboration", "fun, social"]
    images = ["/static/img/python_poster.png", "/static/img/project_meeting.png", "/static/img/yoga_class.jpg"]

    now = datetime.now()
    start_time = now - timedelta(days=30)
    end_range = now + timedelta(days=90)

    sample_events = []

    for i in range(100):
        start_time = random_datetime(start_time,end_range)
        duration_hours = random.randint(1, 3)
        end_time = start_time + timedelta(hours=duration_hours)
        title = titles[i % len(titles)]

        sample_events.append(Events(
            owner_uid=organizer.uid,
            title=title,
            date=start_time.date(),
            start_time=start_time,
            end_time=end_time,
            location=random.choice(locations),
            event_type=random.choice(types),
            organizer=random.choice(organizers),
            tags=random.choice(tags),
            image_urls=random.choice(images),
            description=f"This is a session on {title.lower()}."
        ))

    # old events
    # sample_events = [
    #     Events(
    #         owner_uid=organizer.uid,
    #         title="Intro to Python",
    #         date=now.date(),
    #         start_time=now,
    #         end_time=now + timedelta(hours=1),
    #         location="Room 101",
    #         event_type="Class",
    #         organizer="CS Department",
    #         tags="tech, beginner, python",
    #         image_urls="/static/img/python_poster.png",
    #         description="CS class for beginners"
    #     ),
    #     Events(
    #         owner_uid=organizer.uid,
    #         title="Group Project Meeting",
    #         date=now.date(),
    #         start_time=now + timedelta(days=1, hours=2),
    #         end_time=now + timedelta(days=1, hours=4),
    #         location="Library B12",
    #         event_type="Meeting",
    #         organizer="Project Team",
    #         tags="project, team, collaboration",
    #         image_urls="/static/img/project_meeting.png",
    #         description="Team sync for final project"
    #     ),
    #     Events(
    #         owner_uid=organizer.uid,
    #         title="Yoga Session",
    #         date=now.date(),
    #         start_time=now + timedelta(days=2, hours=1),
    #         end_time=now + timedelta(days=2, hours=2),
    #         location="Wellness Center",
    #         event_type="Gym Class",
    #         organizer="Student Wellness Club",
    #         tags="health, wellness, yoga",
    #         image_urls="/static/img/yoga_class.jpg",
    #         description="Relax and recharge"
    #     )
    # ]

    for event in sample_events:
        event.attendees.append(organizer)  # Add the organizer as an attendee
        event_db.add(event)

    event_db.commit()