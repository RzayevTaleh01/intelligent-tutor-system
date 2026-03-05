from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Text, func, Boolean
from sqlalchemy.orm import relationship
from src.db.base import Base

# --- Multi-tenancy & Auth ---

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True) # UUID or slug
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    users = relationship("User", backref="tenant", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False) # Unique constraint per tenant handled via logic or composite index
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student") # admin, teacher, student
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sessions = relationship("Session", backref="user", cascade="all, delete-orphan")

# --- Background Jobs ---

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True) # UUID
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True) # Optional if system job
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(String, nullable=False) # BUILD_INDEX, etc.
    status = Column(String, default="pending") # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    payload_json = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
