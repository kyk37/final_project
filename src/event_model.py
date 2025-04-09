
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import  declarative_base
from sqlalchemy.ext.declarative import as_declarative

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import as_declarative

@as_declarative()
class Base:
    pass

@as_declarative()
class Base:
    pass

class Events(Base):
    __tablename__ = "events"

    # Primary key column
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str]       = mapped_column(String,  nullable=False)
    time: Mapped[str]        = mapped_column(String,  nullable=True)
    location: Mapped[str]    = mapped_column(String,  nullable=True)
    type: Mapped[str]        = mapped_column(String,  nullable=True)
    description: Mapped[str] = mapped_column(String,  nullable=True)
    event_date: Mapped[str]  = mapped_column(String,  nullable=True)

    def __repr__(self):
        return (
            f"<Events(id={self.id}, title={self.title}, time={self.time}, "
            f"location={self.location}, type={self.type}, "
            f"description={self.description}, event_date={self.event_date})>"
        )
