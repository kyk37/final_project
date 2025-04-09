from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import String, Integer, DateTime

EventBase = declarative_base()

class Events(EventBase):
    __tablename__ = "events"
    uid: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_uid: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[str] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[str] = mapped_column(DateTime, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    def __repr__(self):
        return (f"<Events(title={self.title}, location={self.location}, "
                f"type={self.type}, description={self.description})>")