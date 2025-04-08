from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from src.usr_model import User

def create_admin_user(db: Session):

    try:
        print("bcrypt version:", bcrypt.__version__)
    except AttributeError:
        print("⚠️ bcrypt is broken — reinstall with pip!")

    admin_username = "admin"
    admin_email = "admin@admin.com"
    admin_password = "admin"

    # Check if admin already exists
    existing_user = db.query(User).filter(User.username == admin_username).first()
    if existing_user:
        return

    # Create and add new admin user
    admin_user = User(
        username=admin_username,
        email=admin_email,
        password_hashed=bcrypt.hash(admin_password),
        first_name="Admin",
        last_name="User",
        is_admin=True
    )
    db.add(admin_user)
    db.commit()