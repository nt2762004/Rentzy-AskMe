from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(550), nullable=False)
    content = Column(Text, nullable=False)
    
    # Metadata & Business fields
    record_id = Column(String(100), nullable=True, index=True)
    topic = Column(String(100), nullable=False, index=True)
    sub_topic = Column(String(100), nullable=True, index=True)
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=False, index=True)
    updated_at = Column(String(20), nullable=False) # YYYY-MM-DD
    approver = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    status = Column(String(20), nullable=False, default="active", index=True) # active / inactive

    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    qdrant_point_id = Column(String(100), nullable=False, unique=True, index=True)

    document = relationship("Document", back_populates="chunks")

__table_args__ = (
    Index("idx_doc_status_topic", Document.status, Document.topic),
)
