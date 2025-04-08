
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import  declarative_base
from sqlalchemy.ext.declarative import as_declarative

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import as_declarative

@as_declarative()
class Base:
    pass

class Events(Base):
    __tablename__ = "events"

    title: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    time: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    location: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return (f"<Events(title={self.title}, location={self.location}, "
                f"type={self.type}, description={self.description})>")