from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from shared.database import Base

class TextbookModel(Base):
    """
    SQLAlchemy model representing the 'textbooks' table.
    """
    __tablename__ = "textbooks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    exam_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    parsed_pages: Mapped[List["TextbookParsedPageModel"]] = relationship(
        back_populates="textbook", 
        cascade="all, delete-orphan"
    )
    chunks: Mapped[List["TextbookChunkModel"]] = relationship(
        back_populates="textbook", 
        cascade="all, delete-orphan"
    )


class TextbookParsedPageModel(Base):
    """
    SQLAlchemy model representing the 'textbook_parsed_pages' table.
    Stores extracted raw page text (source of truth).
    """
    __tablename__ = "textbook_parsed_pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Indexed to quickly load pages of a textbook
    textbook_id: Mapped[int] = mapped_column(ForeignKey("textbooks.id"), index=True, nullable=False)
    page_number: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    textbook: Mapped["TextbookModel"] = relationship(back_populates="parsed_pages")

    # Prevent duplicate page entries for the same textbook
    __table_args__ = (
        UniqueConstraint("textbook_id", "page_number", name="uq_textbook_page"),
    )


class TextbookChunkModel(Base):
    """
    SQLAlchemy model representing the 'textbook_chunks' table.
    Stores split text chunks along with high-dimensional vector embeddings for pgvector search.
    """
    __tablename__ = "textbook_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    textbook_id: Mapped[int] = mapped_column(ForeignKey("textbooks.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    concept_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Indexes on subject_name and exam_type for fast metadata filtering during RAG
    subject_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    exam_type: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    
    # 768 dimensions matches Gemini's text-embedding-004 model.
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

    # Relationships
    textbook: Mapped["TextbookModel"] = relationship(back_populates="chunks")


from sqlalchemy import Index  # Ensure Index is imported at the top of database_models.py

class QuestionModel(Base):
    """
    SQLAlchemy model representing the 'questions' table.
    Stores generated and validated multiple-choice questions.
    """
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Link back to source textbook chunk for absolute traceability
    source_chunk_id: Mapped[Optional[int]] = mapped_column(ForeignKey("textbook_chunks.id"), nullable=True)
    
    subject: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    chapter: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    concept: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(50), index=True, default="medium")
    exam_type: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    topic_weightage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    question_type: Mapped[str] = mapped_column(String(50), default="single_correct")
    generated_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    generated_by: Mapped[str] = mapped_column(String(50), default="ai")
    validation_status: Mapped[str] = mapped_column(String(50), default="generated")
    validator_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Admin controls and usage analytics
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    usage_count: Mapped[int] = mapped_column(default=0)
     # 768 dimensions for Gemini text-embedding-004
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(768), nullable=True)

    # Composite Index for multi-field test query compilation (highly optimized search)
    __table_args__ = (
        Index(
            "idx_question_cbt_search", 
            "exam_type", 
            "subject", 
            "chapter", 
            "concept", 
            "difficulty_level"
        ),
    )


