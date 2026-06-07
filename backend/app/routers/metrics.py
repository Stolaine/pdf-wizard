from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import chromadb

from app.config import settings
from app.db.database import get_db, UploadedFile, Conversation, Message
from app.models import UploadedFileOut
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["metrics"])


class CollectionMetric(BaseModel):
    name: str
    count: int


class DatabaseMetricsResponse(BaseModel):
    total_files: int
    total_file_size_bytes: int
    total_conversations: int
    total_messages: int
    status_counts: dict[str, int]
    chroma_collections: list[CollectionMetric]
    files: list[UploadedFileOut]


@router.get("/metrics", response_model=DatabaseMetricsResponse)
async def get_database_metrics(db: Session = Depends(get_db)):
    """Fetch database metrics for files, chats, messages, and Chroma collections."""
    # 1. Fetch SQLite metrics
    total_files = db.query(UploadedFile).count()
    total_file_size_bytes = db.query(func.sum(UploadedFile.file_size)).scalar() or 0
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()

    # Get status counts
    status_counts = {"PENDING": 0, "PROCESSING": 0, "COMPLETED": 0, "CANCELLED": 0, "FAILED": 0}
    status_rows = db.query(UploadedFile.status, func.count(UploadedFile.status)).group_by(UploadedFile.status).all()
    for status, count in status_rows:
        status_counts[status] = count

    # Fetch detailed files list
    files_list = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).all()
    serialized_files = [UploadedFileOut.from_db(f) for f in files_list]

    # 2. Fetch Chroma collections
    chroma_collections = []
    try:
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collections = client.list_collections()
        for col in collections:
            chroma_collections.append(
                CollectionMetric(
                    name=col.name,
                    count=col.count(),
                )
            )
    except Exception as exc:
        logger.warning("Failed to list Chroma collections: %s", exc)

    return DatabaseMetricsResponse(
        total_files=total_files,
        total_file_size_bytes=total_file_size_bytes,
        total_conversations=total_conversations,
        total_messages=total_messages,
        status_counts=status_counts,
        chroma_collections=chroma_collections,
        files=serialized_files,
    )
