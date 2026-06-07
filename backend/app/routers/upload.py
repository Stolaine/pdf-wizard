import os
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db, Conversation
from app.models import UploadResponse
from app.services import pdf_service, vector_service, history_service, file_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    create_conversation: bool = True,
    background_tasks: BackgroundTasks = BackgroundTasks(),
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

    # ── Check Duplicate Ingestion ───────────────────────────────────────
    os.makedirs(settings.uploads_dir, exist_ok=True)
    save_path = os.path.join(settings.uploads_dir, file.filename)

    existing_file = file_service.get_file_by_filename(db, file.filename)
    if existing_file:
        if existing_file.status in ("COMPLETED", "PENDING", "PROCESSING") and os.path.exists(save_path):
            logger.info(
                "PDF '%s' already exists in local storage and database with status '%s'. Reusing...",
                file.filename,
                existing_file.status,
            )
            conv_id = ""
            if create_conversation:
                conversation = history_service.create_conversation(
                    db=db,
                    pdf_name=file.filename,
                    collection_name=existing_file.collection_name,
                    file_id=existing_file.id,
                )
                conv_id = conversation.id
            return UploadResponse(
                filename=file.filename,
                num_chunks=existing_file.num_chunks,
                collection_name=existing_file.collection_name,
                conversation_id=conv_id,
                file_id=existing_file.id,
                message=f"PDF already exists (status: {existing_file.status}), starting new conversation." if create_conversation else "PDF already exists."
            )
        else:
            # Clean up the failed/cancelled/stale file first to avoid unique constraint violations
            file_service.delete_file(db, existing_file.id)

    # ── Save PDF to local storage ───────────────────────────────────────
    try:
        with open(save_path, "wb") as f:
            f.write(file_bytes)
    except Exception as exc:
        logger.exception("Failed to save PDF to local storage")
        raise HTTPException(status_code=500, detail=f"Failed to write file to local disk: {exc}")

    # ── Parse pages count ───────────────────────────────────────────────
    import io
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        num_pages = len(reader.pages)
    except Exception as exc:
        logger.exception("Failed to parse PDF pages")
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF metadata: {exc}")

    file_size = len(file_bytes)

    # ── Register UploadedFile in PENDING state ──────────────────────────
    uploaded_file = file_service.create_file_metadata(
        db=db,
        filename=file.filename,
        file_size=file_size,
        num_pages=num_pages,
        chunk_size=settings.chunk_size,
        overlap_size=settings.chunk_overlap,
        embedding_model=settings.embedding_model,
    )

    # ── Create conversation if requested ────────────────────────────────
    conv_id = ""
    if create_conversation:
        conversation = history_service.create_conversation(
            db=db,
            pdf_name=file.filename,
            collection_name=uploaded_file.collection_name,
            file_id=uploaded_file.id,
        )
        conv_id = conversation.id

        # ── Launch background chat title generation task ──────────────────
        background_tasks.add_task(
            history_service.generate_chat_name_task,
            conversation_id=conversation.id,
            file_id=uploaded_file.id,
        )

    # ── Launch background embedding task ───────────────────────────────
    background_tasks.add_task(
        file_service.process_embedding_task,
        file_id=uploaded_file.id,
        file_path=save_path,
    )

    logger.info(
        "Started background tasks for '%s': collection '%s', conversation '%s'",
        file.filename,
        uploaded_file.collection_name,
        conv_id,
    )

    return UploadResponse(
        filename=file.filename,
        num_chunks=0,
        collection_name=uploaded_file.collection_name,
        conversation_id=conv_id,
        file_id=uploaded_file.id,
        message="PDF upload successful, starting background embedding..."
    )


