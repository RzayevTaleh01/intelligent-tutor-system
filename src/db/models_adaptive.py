from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Text, func
from sqlalchemy.orm import relationship
from src.db.base import Base

class LearnerSkill(Base):
    __tablename__ = "learner_skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    skill_tag = Column(String, nullable=False)
    
    # BKT Parameters
    p_mastery = Column(Float, default=0.1) # Initial mastery
    p_learn = Column(Float, default=0.1)   # Learning rate
    p_slip = Column(Float, default=0.1)    # Slip probability
    p_guess = Column(Float, default=0.2)   # Guess probability
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class LearnerSchedule(Base):
    __tablename__ = "learner_schedule"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    skill_tag = Column(String, nullable=False)
    
    due_at = Column(DateTime(timezone=True), nullable=False)
    interval_days = Column(Float, default=1.0)
    ease = Column(Float, default=2.5) # SM-2 ease factor
    repetitions = Column(Integer, default=0)

class LearnerError(Base):
    __tablename__ = "learner_errors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    skill_tag = Column(String, nullable=False)
    error_code = Column(String, nullable=False)
    
    count = Column(Integer, default=1)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
