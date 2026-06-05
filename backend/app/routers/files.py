"""Files router — handles listing, deleting, and starting chats from uploaded PDFs."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import UploadedFileOut, ConversationSummary
from app.services import file_service, history_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files", response_model=list[UploadedFileOut])
async def list_files(db: Session = Depends(get_db)):
    """List all uploaded PDF files in the database."""
    files = file_service.get_files(db)
    return [UploadedFileOut.from_db(f) for f in files]


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete an uploaded PDF file from database, disk, and vector store."""
    success = file_service.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found.")
    return {"status": "success", "message": "File and related conversations deleted successfully."}


@router.post("/files/{file_id}/cancel")
async def cancel_file_embedding(file_id: str, db: Session = Depends(get_db)):
    """Cancel an ongoing file embedding process."""
    uploaded_file = file_service.get_file(db, file_id)
    if uploaded_file is None:
        raise HTTPException(status_code=404, detail="File not found.")

    if uploaded_file.status not in ["PENDING", "PROCESSING"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel embedding for a file with status '{uploaded_file.status}'."
        )

    uploaded_file.status = "CANCELLED"
    db.commit()
    logger.info("Cancelled ongoing embedding task for file '%s'", file_id)
    return {"status": "success", "message": "Embedding cancellation requested."}


@router.post("/files/{file_id}/conversations", response_model=ConversationSummary)
async def start_new_conversation(file_id: str, db: Session = Depends(get_db)):
    """Start a new chat conversation using an already uploaded PDF file."""
    uploaded_file = file_service.get_file(db, file_id)
    if uploaded_file is None:
        raise HTTPException(status_code=404, detail="File not found.")

    conversation = history_service.create_conversation(
        db=db,
        pdf_name=uploaded_file.filename,
        collection_name=uploaded_file.collection_name,
        file_id=uploaded_file.id,
    )

    logger.info(
        "Started new conversation '%s' for existing file '%s' (collection '%s')",
        conversation.id,
        uploaded_file.filename,
        uploaded_file.collection_name,
    )

    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        pdf_name=conversation.pdf_name,
        collection_name=conversation.collection_name,
        created_at=conversation.created_at,
        files=[UploadedFileOut.from_db(uploaded_file)],
    )


@router.post("/conversations/{conversation_id}/files/{file_id}", response_model=ConversationSummary)
async def link_file_to_conversation(
    conversation_id: str,
    file_id: str,
    db: Session = Depends(get_db),
):
    """Associate an existing uploaded PDF with an ongoing conversation context."""
    conversation = history_service.add_file_to_conversation(db, conversation_id, file_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation or File not found.")

    logger.info(
        "Linked file '%s' to conversation '%s'",
        file_id,
        conversation_id,
    )

    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        pdf_name=conversation.pdf_name,
        collection_name=conversation.collection_name,
        created_at=conversation.created_at,
        files=[UploadedFileOut.from_db(f) for f in conversation.files],
    )
