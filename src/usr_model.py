from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import as_declarative
from dataclasses import dataclass
from typing import ClassVar

from sqlalchemy import Boolean


@as_declarative()
class Base:
    pass

class User(Base):
    __tablename__ = "users"
    uid: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hashed: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at:Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    about: Mapped[str] = mapped_column(String, nullable=True)
    
    def __repr__(self):
        return f"<User(name={self.__class__.__name__}, admin={self.is_admin} username={self.username}, email: {self.email}, password: {self.password_hashed}"

@dataclass
class UserInDB(User):
    hashed_pass: ClassVar[str]


def get_user(db, username:str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
