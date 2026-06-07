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


def generate_chat_name_task(conversation_id: str, file_id: str) -> None:
    """Generate a chat name using LLM based on the first file's content."""
    import os
    import logging
    from app.db.database import SessionLocal, Conversation, UploadedFile
    from app.config import settings

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        # Fetch conversation and file
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not conv or not uploaded_file:
            logger.warning("Conversation %s or File %s not found for title generation", conversation_id, file_id)
            return

        # Read file text
        file_path = os.path.join(settings.uploads_dir, uploaded_file.filename)
        if not os.path.exists(file_path):
            logger.warning("File %s does not exist on disk", file_path)
            return

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Extract text using pdf_service
        from app.services import pdf_service
        text = pdf_service.extract_text(file_bytes)
        
        # Take the first 2000 characters as context
        sample_text = text[:2000]

        # Call LLM to generate a short title
        from app.services import qa_service
        llm = qa_service._get_llm()

        prompt = (
            f"Based on the following start of a document, generate a very short, descriptive "
            f"title for a conversation about it. The title must be between 2 and 5 words, "
            f"and contain absolutely no quotes, no markdown, and no preamble. Just return the title.\n\n"
            f"Document Start:\n{sample_text}\n\n"
            f"Title:"
        )

        logger.info("Generating chat name for conversation %s...", conversation_id)
        raw_title = llm.invoke(prompt)
        
        # Handle prompt echo
        if prompt in raw_title:
            generated_title = raw_title.replace(prompt, "").strip()
        elif "Title:" in raw_title:
            generated_title = raw_title.split("Title:")[-1].strip()
        else:
            generated_title = raw_title.strip()

        # Clean title
        generated_title = generated_title.split("\n")[0].strip()
        generated_title = generated_title.strip('`"\'[]{}')

        # Clean specific prefixes if LLM still hallucinated them
        for prefix in ["Title:", "chat title:", "Chat Title:"]:
            if generated_title.lower().startswith(prefix.lower()):
                generated_title = generated_title[len(prefix):].strip()

        if generated_title:
            conv.title = generated_title
            db.commit()
            logger.info("Updated title for conversation %s to '%s'", conversation_id, generated_title)
    except Exception as exc:
        logger.exception("Failed to generate chat name for conversation %s", conversation_id)
    finally:
        db.close()


def update_conversation_title(db: Session, conversation_id: str, title: str) -> Conversation | None:
    """Update the title of a conversation."""
    conv = get_conversation(db, conversation_id)
    if conv is None:
        return None
    conv.title = title
    db.commit()
    db.refresh(conv)
    return conv
