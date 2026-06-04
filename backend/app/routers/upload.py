"""Upload router — handles PDF file uploads and processing."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models import UploadResponse
from app.services import pdf_service, vector_service, history_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF, extract text, create embeddings, store in ChromaDB."""

    # ── Validate ────────────────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()

    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_bytes // (1024 * 1024)} MB.",
        )

    # ── Extract text ────────────────────────────────────────────────────
    try:
        text = pdf_service.extract_text(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # ── Chunk + embed ───────────────────────────────────────────────────
    documents = vector_service.chunk_text(text)
    collection_name = f"pdf_{uuid.uuid4().hex[:12]}"
    vector_service.store_embeddings(documents, collection_name)

    # ── Create conversation ─────────────────────────────────────────────
    conversation = history_service.create_conversation(
        db=db,
        pdf_name=file.filename,
        collection_name=collection_name,
    )

    logger.info(
        "Processed '%s': %d chunks → collection '%s', conversation '%s'",
        file.filename,
        len(documents),
        collection_name,
        conversation.id,
    )

    return UploadResponse(
        filename=file.filename,
        num_chunks=len(documents),
        collection_name=collection_name,
        conversation_id=conversation.id,
    )
