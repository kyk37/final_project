from sqlalchemy import Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from dataclasses import dataclass
from typing import ClassVar

from src.event_model import event_signups#, Events,

from db.base import Base

class User(Base):
    __tablename__ = "users"

    uid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hashed: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False)
    about: Mapped[str] = mapped_column(String, nullable=True)
    profile_image_url: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default="/static/defaults/default_avatar.jpg"
    )

    events: Mapped[list["Events"]] = relationship(
        "Events",
        secondary=event_signups,
        back_populates="attendees"
    )

    def __repr__(self):
        return (
            f"<User(name={self.__class__.__name__}, "
            f"organizer={self.is_organizer}, "
            f"username={self.username}, "
            f"email={self.email})>"
            f"password={self.password_hashed})>"
        )
    


@dataclass
class UserInDB(User):
    hashed_pass: ClassVar[str]
    
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
