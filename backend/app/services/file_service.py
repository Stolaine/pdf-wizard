"""Database and disk operations for uploaded files, including background tasks."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import UploadedFile, SessionLocal
from app.services import vector_service, pdf_service

logger = logging.getLogger(__name__)


def create_file_metadata(
    db: Session,
    filename: str,
    file_size: int,
    num_pages: int,
    chunk_size: int,
    overlap_size: int,
    embedding_model: str,
) -> UploadedFile:
    """Create an initial UploadedFile record in PENDING state."""
    collection_name = f"pdf_{uuid.uuid4().hex[:12]}"
    uploaded_file = UploadedFile(
        id=str(uuid.uuid4()),
        filename=filename,
        collection_name=collection_name,
        num_chunks=0,
        created_at=datetime.now(timezone.utc),
        file_size=file_size,
        num_pages=num_pages,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        status="PENDING",
        progress=0,
        embedding_model=embedding_model,
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    return uploaded_file


def get_files(db: Session) -> list[UploadedFile]:
    """Retrieve all uploaded files, sorted by creation time descending."""
    return db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).all()


def get_file(db: Session, file_id: str) -> UploadedFile | None:
    """Retrieve a single uploaded file by its ID."""
    return db.query(UploadedFile).filter(UploadedFile.id == file_id).first()


def get_file_by_filename(db: Session, filename: str) -> UploadedFile | None:
    """Retrieve an uploaded file by its filename."""
    return db.query(UploadedFile).filter(UploadedFile.filename == filename).first()


def delete_file(db: Session, file_id: str) -> bool:
    """Delete an uploaded file from database, disk, and vector store.

    Cascading deletion will also remove all linked conversations and messages.
    """
    uploaded_file = get_file(db, file_id)
    if uploaded_file is None:
        return False

    # 1. Update status to CANCELLED first to abort background task if running
    if uploaded_file.status in ["PENDING", "PROCESSING"]:
        uploaded_file.status = "CANCELLED"
        db.commit()

    # 2. Delete physical file from local uploads directory
    local_path = os.path.join(settings.uploads_dir, uploaded_file.filename)
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
            logger.info("Deleted physical file '%s' from local storage", local_path)
        except Exception as exc:
            logger.exception("Failed to delete physical file '%s'", local_path)

    # 3. Delete ChromaDB collection
    try:
        vector_service.delete_collection(uploaded_file.collection_name)
    except Exception as exc:
        logger.warning(
            "Could not delete Chroma collection '%s' for file: %s",
            uploaded_file.collection_name,
            exc,
        )

    # 4. Delete from DB (Conversation and Messages will cascade delete)
    db.delete(uploaded_file)
    db.commit()
    logger.info("Deleted UploadedFile record '%s' and cascaded related conversations", file_id)
    return True


def process_embedding_task(file_id: str, file_path: str) -> None:
    """FastAPI background task to extract, chunk, and embed a PDF in the background.

    Allows self-cancellation if DB status is changed to CANCELLED.
    """
    logger.info("Starting background embedding task for file_id='%s'", file_id)
    start_time = datetime.now(timezone.utc)
    db = SessionLocal()

    try:
        # 1. Update status to PROCESSING
        db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not db_file:
            logger.error("UploadedFile not found for file_id='%s'", file_id)
            return

        db_file.status = "PROCESSING"
        db_file.embedding_start_time = start_time
        db_file.progress = 5
        db.commit()

        # 2. Read physical file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Physical file missing at {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        db_file.progress = 10
        db.commit()

        # Check for cancellation
        db.refresh(db_file)
        if db_file.status == "CANCELLED":
            logger.info("Embedding task for file '%s' was cancelled before text extraction.", file_id)
            return

        # 3. Extract text
        text = pdf_service.extract_text(file_bytes)

        db_file.progress = 15
        db.commit()

        # Check for cancellation
        db.refresh(db_file)
        if db_file.status == "CANCELLED":
            logger.info("Embedding task for file '%s' was cancelled before chunking.", file_id)
            return

        # 4. Chunk text
        documents = vector_service.chunk_text(text)
        db_file.num_chunks = len(documents)
        db_file.progress = 25
        db.commit()

        # Check for cancellation
        db.refresh(db_file)
        if db_file.status == "CANCELLED":
            logger.info("Embedding task for file '%s' was cancelled after chunking.", file_id)
            return

        if len(documents) == 0:
            raise ValueError("No extractable chunks found in the PDF.")

        # 5. Generate and store embeddings in batches
        from langchain_chroma import Chroma
        embeddings_impl = vector_service._get_embeddings()
        
        # Determine vector size (dimension) and update DB
        # BGE-small-en-v1.5 has size 384
        db_file.vector_size = 384
        db.commit()

        total_docs = len(documents)
        batch_size = 20
        vectorstore = None

        for i in range(0, total_docs, batch_size):
            # Check for cancellation inside the loop
            db.refresh(db_file)
            if db_file.status == "CANCELLED":
                logger.info("Embedding task for file '%s' was cancelled during embedding loop.", file_id)
                try:
                    vector_service.delete_collection(db_file.collection_name)
                except Exception:
                    pass
                return

            batch = documents[i : i + batch_size]
            if vectorstore is None:
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings_impl,
                    collection_name=db_file.collection_name,
                    persist_directory=settings.chroma_persist_dir,
                )
            else:
                vectorstore.add_documents(batch)

            processed = min(i + batch_size, total_docs)
            percent = int(25 + (processed / total_docs) * 70)  # progress ranges 25% to 95%
            db_file.progress = percent
            db.commit()

        # 6. Complete task
        end_time = datetime.now(timezone.utc)
        time_taken = (end_time - start_time).total_seconds()

        db_file.status = "COMPLETED"
        db_file.progress = 100
        db_file.embedding_end_time = end_time
        db_file.time_taken = time_taken
        db.commit()
        logger.info("Successfully finished background embedding task for '%s' in %.2fs", db_file.filename, time_taken)

    except Exception as exc:
        logger.exception("Failed background embedding task for file '%s'", file_id)
        try:
            db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
            if db_file:
                db_file.status = "FAILED"
                db_file.progress = 100
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
