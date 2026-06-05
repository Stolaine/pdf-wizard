"""Tools for processing and embedding PDFs."""

from __future__ import annotations

import logging
import os
import shutil
import uuid
from pathlib import Path

from langchain_core.tools import tool

from app.config import settings
from app.db.database import SessionLocal, Conversation
from app.services import pdf_service, vector_service, history_service

logger = logging.getLogger(__name__)


@tool
def embed_pdf(file_path: str) -> dict:
    """Extracts text from a PDF file, chunks it, generates embeddings, and stores them in ChromaDB.

    Args:
        file_path: The absolute or relative path to the PDF file on the server.

    Returns:
        A dictionary with the following keys:
        - status: "success" or "error"
        - filename: The name of the processed PDF file.
        - num_chunks: The number of text chunks created.
        - collection_name: The name of the ChromaDB collection.
        - conversation_id: The ID of the database conversation record.
        - message: A descriptive success or error message.
    """
    logger.info("Tool embed_pdf called with file_path: '%s'", file_path)

    path = Path(file_path)
    filename = path.name

    # Validate file type
    if not filename.lower().endswith(".pdf"):
        msg = "Only PDF files are supported."
        logger.error(msg)
        return {
            "status": "error",
            "filename": filename,
            "num_chunks": 0,
            "collection_name": "",
            "conversation_id": "",
            "message": msg,
        }

    # Setup local storage path
    os.makedirs(settings.uploads_dir, exist_ok=True)
    local_storage_path = os.path.join(settings.uploads_dir, filename)

    # ── Check Duplicate Ingestion ───────────────────────────────────────
    try:
        with SessionLocal() as db:
            existing_conv = db.query(Conversation).filter(Conversation.pdf_name == filename).first()
            if existing_conv and os.path.exists(local_storage_path):
                logger.info(
                    "Tool embed_pdf: PDF '%s' already exists in local storage and database. Reusing collection '%s'",
                    filename,
                    existing_conv.collection_name,
                )
                return {
                    "status": "success",
                    "filename": filename,
                    "num_chunks": 0,
                    "collection_name": existing_conv.collection_name,
                    "conversation_id": existing_conv.id,
                    "message": "PDF already processed, reusing existing conversation.",
                }
    except Exception as exc:
        logger.warning("Duplicate check failed: %s. Proceeding with ingestion.", exc)

    # Validate source file existence
    if not path.exists():
        msg = f"Source file not found at: {file_path}"
        logger.error(msg)
        return {
            "status": "error",
            "filename": filename,
            "num_chunks": 0,
            "collection_name": "",
            "conversation_id": "",
            "message": msg,
        }

    try:
        # Copy file to local storage if it's not already there
        if not os.path.exists(local_storage_path):
            shutil.copy2(path, local_storage_path)
            logger.info("Copied '%s' to local storage uploads directory", filename)

        # Read the file bytes
        with open(local_storage_path, "rb") as f:
            file_bytes = f.read()

        # Extract text
        text = pdf_service.extract_text(file_bytes)

        # Chunk text
        documents = vector_service.chunk_text(text)

        # Generate collection name
        collection_name = f"pdf_{uuid.uuid4().hex[:12]}"

        # Store embeddings
        vector_service.store_embeddings(documents, collection_name)

        # Create conversation record
        with SessionLocal() as db:
            conversation = history_service.create_conversation(
                db=db,
                pdf_name=filename,
                collection_name=collection_name,
            )
            conversation_id = conversation.id

        logger.info(
            "Tool embed_pdf successfully processed '%s': %d chunks -> collection '%s', conversation '%s'",
            filename,
            len(documents),
            collection_name,
            conversation_id,
        )

        return {
            "status": "success",
            "filename": filename,
            "num_chunks": len(documents),
            "collection_name": collection_name,
            "conversation_id": conversation_id,
            "message": "PDF processed and embedded successfully.",
        }

    except Exception as exc:
        msg = f"Failed to embed PDF: {exc}"
        logger.exception(msg)
        return {
            "status": "error",
            "filename": filename,
            "num_chunks": 0,
            "collection_name": "",
            "conversation_id": "",
            "message": msg,
        }
