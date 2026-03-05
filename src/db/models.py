from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Text, func
from sqlalchemy.orm import relationship
from src.db.base import Base
from src.db.models_knowledge import KnowledgeSource, KnowledgeChunk, KnowledgeEmbedding, KnowledgeTopic, KnowledgeEdge
from src.db.models_adaptive import LearnerSkill, LearnerSchedule, LearnerError, AnalyticsEvent
from src.db.models_diagnostics import LearnerTheta, LearnerThetaSkill, SkillDifficulty, BanditArm, ExperimentAssignment, ConceptNode, ConceptEdge
from src.db.models_prod import Tenant, User, Job

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True) # Added for v2
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Added for v2
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    skills = relationship("LearnerSkill", backref="session", cascade="all, delete-orphan")
    schedule = relationship("LearnerSchedule", backref="session", cascade="all, delete-orphan")
    errors = relationship("LearnerError", backref="session", cascade="all, delete-orphan")
    analytics = relationship("AnalyticsEvent", backref="session", cascade="all, delete-orphan")
    
    # Diagnostics
    theta = relationship("LearnerTheta", uselist=False, backref="session", cascade="all, delete-orphan")
    theta_skills = relationship("LearnerThetaSkill", backref="session", cascade="all, delete-orphan")
    experiment = relationship("ExperimentAssignment", uselist=False, backref="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LearnerState(Base):
    __tablename__ = "learner_states"
    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    mastery_score = Column(Float, default=0.5)
    readiness_score = Column(Float, default=0.5)
    recent_errors = Column(JSON, default=list)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    event_type = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
