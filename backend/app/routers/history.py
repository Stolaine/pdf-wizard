"""History router — list and retrieve past conversations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import ConversationDetail, ConversationSummary, MessageOut, UploadedFileOut
from app.services import history_service

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(db: Session = Depends(get_db)):
    """Return all conversations (newest first)."""
    convos = history_service.get_conversations(db)
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            pdf_name=c.pdf_name,
            collection_name=c.collection_name,
            created_at=c.created_at,
            files=[UploadedFileOut.from_db(f) for f in c.files],
        )
        for c in convos
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Return a single conversation with all its messages."""
    conv = history_service.get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        pdf_name=conv.pdf_name,
        collection_name=conv.collection_name,
        created_at=conv.created_at,
        files=[UploadedFileOut.from_db(f) for f in conv.files],
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                thinking=m.thinking,
                created_at=m.created_at,
            )
            for m in conv.messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    deleted = history_service.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"detail": "Conversation deleted."}
