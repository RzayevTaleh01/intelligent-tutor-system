from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.session import Base

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    learner_state: Mapped["LearnerState"] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    role: Mapped[str] = mapped_column(String)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    session: Mapped["Session"] = relationship(back_populates="messages")

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    event_type: Mapped[str] = mapped_column(String) # assessment, pedagogical_decision, error
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship(back_populates="events")

class LearnerState(Base):
    __tablename__ = "learner_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), unique=True)
    
    mastery_score: Mapped[float] = mapped_column(Float, default=0.5)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.5)
    recent_errors: Mapped[dict] = mapped_column(JSON, default=list) # Storing list of strings as JSON
    current_topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    session: Mapped["Session"] = relationship(back_populates="learner_state")
