"""SQLAlchemy database setup for conversation / message persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class Conversation(Base):
    """A conversation tied to an uploaded PDF."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, default="New conversation")
    pdf_name = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
