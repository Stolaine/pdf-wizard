"""Pydantic models (schemas) shared across the API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Upload ──────────────────────────────────────────────────────────────────

class UploadedFileOut(BaseModel):
    """Metadata representing an uploaded PDF file."""

    id: str
    filename: str
    collection_name: str
    num_chunks: int
    created_at: datetime
    file_size: int
    num_pages: int
    chunk_size: int
    overlap_size: int
    vector_size: Optional[int] = None
    embedding_model: Optional[str] = None
    time_taken: Optional[float] = None
    embedding_start_time: Optional[datetime] = None
    embedding_end_time: Optional[datetime] = None
    status: str
    progress: int

    @classmethod
    def from_db(cls, f) -> UploadedFileOut:
        return cls(
            id=f.id,
            filename=f.filename,
            collection_name=f.collection_name,
            num_chunks=f.num_chunks,
            created_at=f.created_at,
            file_size=f.file_size,
            num_pages=f.num_pages,
            chunk_size=f.chunk_size,
            overlap_size=f.overlap_size,
            vector_size=f.vector_size,
            embedding_model=f.embedding_model,
            time_taken=f.time_taken,
            embedding_start_time=f.embedding_start_time,
            embedding_end_time=f.embedding_end_time,
            status=f.status,
            progress=f.progress,
        )



class UploadResponse(BaseModel):
    """Returned after a successful PDF upload & embedding."""

    filename: str
    num_chunks: int
    collection_name: str
    conversation_id: str
    file_id: str
    message: str = "PDF processed successfully"


# ── Query ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Incoming question from the user."""

    question: str
    conversation_id: str
    collection_name: Optional[str] = None



class SourceChunk(BaseModel):
    """A snippet of the source document used for the answer."""

    content: str
    page: Optional[int] = None


class QueryResponse(BaseModel):
    """Answer returned to the user."""

    answer: str
    conversation_id: str
    sources: list[SourceChunk] = Field(default_factory=list)
    thinking: Optional[str] = None


# ── Conversation history ────────────────────────────────────────────────────

class MessageOut(BaseModel):
    """A single message in a conversation."""

    id: int
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime
    thinking: Optional[str] = None


class ConversationSummary(BaseModel):
    """Lightweight representation for the sidebar list."""

    id: str
    title: str
    pdf_name: Optional[str] = None
    collection_name: Optional[str] = None
    created_at: datetime
    files: list[UploadedFileOut] = Field(default_factory=list)


class ConversationDetail(BaseModel):
    """Full conversation including messages."""

    id: str
    title: str
    pdf_name: Optional[str] = None
    collection_name: Optional[str] = None
    created_at: datetime
    files: list[UploadedFileOut] = Field(default_factory=list)
    messages: list[MessageOut] = Field(default_factory=list)


