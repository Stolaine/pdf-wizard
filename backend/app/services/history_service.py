"""Conversation history persistence backed by SQLite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.database import Conversation, Message


# ── Create ──────────────────────────────────────────────────────────────────

def create_conversation(
    db: Session,
    pdf_name: str,
    collection_name: str,
    file_id: str | None = None,
    file_ids: list[str] | None = None,
) -> Conversation:
    """Create a new conversation record and link it to uploaded files."""
    ids_to_fetch = []
    if file_id:
        ids_to_fetch.append(file_id)
    if file_ids:
        ids_to_fetch.extend(file_ids)

    files_list = []
    if ids_to_fetch:
        from app.db.database import UploadedFile
        files_list = db.query(UploadedFile).filter(UploadedFile.id.in_(ids_to_fetch)).all()

    conv = Conversation(
        id=str(uuid.uuid4()),
        title=pdf_name,
        pdf_name=pdf_name,
        collection_name=collection_name,
        files=files_list,
        created_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def add_file_to_conversation(
    db: Session,
    conversation_id: str,
    file_id: str,
) -> Conversation | None:
    """Associate an uploaded file with an existing conversation."""
    from app.db.database import UploadedFile
    conv = get_conversation(db, conversation_id)
    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()

    if conv is None or uploaded_file is None:
        return None

    if uploaded_file not in conv.files:
        conv.files.append(uploaded_file)
        db.commit()
        db.refresh(conv)
    return conv


# ── Messages ────────────────────────────────────────────────────────────────

def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    thinking: str | None = None,
) -> Message:
    """Append a message to an existing conversation."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        thinking=thinking,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ── Read ────────────────────────────────────────────────────────────────────

def get_conversations(db: Session) -> list[Conversation]:
    """Return all conversations ordered by most recent first."""
    return (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc())
        .all()
    )


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    """Return a single conversation with its messages, or None."""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def delete_conversation(db: Session, conversation_id: str) -> bool:
    """Delete a conversation and all its messages. Returns True if found."""
    conv = get_conversation(db, conversation_id)
    if conv is None:
        return False
    db.delete(conv)
    db.commit()
    return True
