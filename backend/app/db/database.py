"""SQLAlchemy database setup for conversation / message persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Table, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# Junction table for many-to-many relationship between Conversations and UploadedFiles
conversation_files = Table(
    "conversation_files",
    Base.metadata,
    Column("conversation_id", String, ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", String, ForeignKey("uploaded_files.id", ondelete="CASCADE"), primary_key=True),
)


class UploadedFile(Base):
    """A record of a locally saved PDF file with embedding status."""

    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False, unique=True)
    collection_name = Column(String, nullable=False, unique=True)
    num_chunks = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    file_size = Column(Integer, nullable=False, default=0)
    num_pages = Column(Integer, nullable=False, default=0)
    chunk_size = Column(Integer, nullable=False, default=0)
    overlap_size = Column(Integer, nullable=False, default=0)
    vector_size = Column(Integer, nullable=True)
    embedding_model = Column(String, nullable=True)
    time_taken = Column(Float, nullable=True)
    embedding_start_time = Column(DateTime, nullable=True)
    embedding_end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    progress = Column(Integer, nullable=False, default=0)

    conversations = relationship(
        "Conversation",
        secondary=conversation_files,
        back_populates="files",
    )



class Conversation(Base):
    """A conversation tied to one or more uploaded PDFs."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, default="New conversation")
    pdf_name = Column(String, nullable=True)
    collection_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    files = relationship(
        "UploadedFile",
        secondary=conversation_files,
        back_populates="conversations",
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )



class Message(Base):
    """An individual message (user or assistant) inside a conversation."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


# ── Engine & session factory ────────────────────────────────────────────────

engine = create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency – yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Event Listeners ─────────────────────────────────────────────────────────

from sqlalchemy import event
import os
import logging

@event.listens_for(UploadedFile, 'after_delete')
def cleanup_file_resources(mapper, connection, target):
    """Ensure local disk PDF and Chroma collection are deleted when UploadedFile is deleted."""
    logger = logging.getLogger(__name__)
    
    # 1. Delete physical file
    local_path = os.path.join(settings.uploads_dir, target.filename)
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
            logger.info("Event listener deleted physical file '%s' from local storage", local_path)
        except Exception:
            logger.exception("Event listener failed to delete physical file '%s'", local_path)

    # 2. Delete ChromaDB collection
    try:
        from app.services import vector_service
        vector_service.delete_collection(target.collection_name)
        logger.info("Event listener successfully deleted Chroma collection '%s'", target.collection_name)
    except Exception as exc:
        logger.warning(
            "Event listener could not delete Chroma collection '%s': %s",
            target.collection_name,
            exc,
        )
