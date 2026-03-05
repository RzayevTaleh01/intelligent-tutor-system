from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Text, func
from sqlalchemy.orm import relationship
from src.db.base import Base

# Concept Graph
class ConceptNode(Base):
    __tablename__ = "concept_nodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_tag = Column(String, unique=True, nullable=False)

class ConceptEdge(Base):
    __tablename__ = "concept_edges"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_skill_tag = Column(String, ForeignKey("concept_nodes.skill_tag"), nullable=False)
    to_skill_tag = Column(String, ForeignKey("concept_nodes.skill_tag"), nullable=False)
    weight = Column(Float, default=0.5)

# Cognitive Diagnostics (IRT)
class LearnerTheta(Base):
    __tablename__ = "learner_theta"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    theta_overall = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class LearnerThetaSkill(Base):
    __tablename__ = "learner_theta_skill"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    skill_tag = Column(String, nullable=False)
    theta = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SkillDifficulty(Base):
    __tablename__ = "skill_difficulty"
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_tag = Column(String, nullable=False)
    item_type = Column(String, nullable=False) # e.g. "mcq", "vocab_fill"
    b = Column(Float, default=0.0) # Difficulty parameter
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Bandit Optimizer
class BanditArm(Base):
    __tablename__ = "bandit_arms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    arm_key = Column(String, unique=True, nullable=False) # "skill_tag|item_type|difficulty_bucket"
    pulls = Column(Integer, default=0)
    reward_sum = Column(Float, default=0.0)
    reward_sq_sum = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# A/B Experiments
class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), unique=True, nullable=False)
    variant = Column(String, nullable=False) # "A" or "B"
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
