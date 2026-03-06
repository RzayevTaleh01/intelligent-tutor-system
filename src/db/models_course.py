from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from src.db.base import Base

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True) # UUID
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    
    # Configuration for the GenericPlugin (e.g. prompt templates, difficulty rules)
    settings = Column(JSON, default={})
    
    is_active = Column(Integer, default=1) # 1=Active, 0=Archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    knowledge_sources = relationship("KnowledgeSource", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="course")
