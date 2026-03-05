from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, LargeBinary, Text
from sqlalchemy.orm import relationship
from src.db.base import Base

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    filetype = Column(String, nullable=False)
    created_at = Column(Float, nullable=False)
    
    chunks = relationship("KnowledgeChunk", back_populates="source", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("knowledge_sources.id"), nullable=False)
    position = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    meta_json = Column(JSON, nullable=True)
    
    source = relationship("KnowledgeSource", back_populates="chunks")
    embedding = relationship("KnowledgeEmbedding", uselist=False, back_populates="chunk", cascade="all, delete-orphan")

class KnowledgeEmbedding(Base):
    __tablename__ = "knowledge_embeddings"
    
    chunk_id = Column(String, ForeignKey("knowledge_chunks.id"), primary_key=True)
    vector = Column(LargeBinary, nullable=False) # numpy float32 bytes
    dim = Column(Integer, nullable=False)
    
    chunk = relationship("KnowledgeChunk", back_populates="embedding")

class KnowledgeTopic(Base):
    __tablename__ = "knowledge_topics"
    
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("knowledge_sources.id"), nullable=False)
    name = Column(String, nullable=False)

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("knowledge_sources.id"), nullable=False)
    from_chunk_id = Column(String, ForeignKey("knowledge_chunks.id"), nullable=False)
    to_chunk_id = Column(String, ForeignKey("knowledge_chunks.id"), nullable=False)
    weight = Column(Float, default=1.0)
