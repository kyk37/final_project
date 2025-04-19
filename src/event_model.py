from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy import String, Integer, DateTime, Table, ForeignKey, Column
from db.base import Base
from sqlalchemy import JSON

event_signups = Table(
    'event_signups',
    Base.metadata,
    Column('event_id', ForeignKey('events.uid'), primary_key=True),
    Column('user_id', ForeignKey('users.uid'), primary_key=True)
)

class Events(Base):
    __tablename__ = "events"

    uid: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_uid: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=True)
    organizer: Mapped[str] = mapped_column(String, nullable=True, default="Unknown")
    tags: Mapped[str] = mapped_column(String, nullable=True, default="")
    image_urls: Mapped[str] = mapped_column(String, nullable=True, default="")
    description: Mapped[str] = mapped_column(String, nullable=True)

    attendees: Mapped[list["User"]] = relationship(
        "User",
        secondary="event_signups",
        back_populates="events"
    )

    def __repr__(self):
        return (
            f"<Events(title={self.title}, location={self.location}, "
            f"event_type={self.event_type}, description={self.description})>"
        )