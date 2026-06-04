"""Pydantic models (schemas) shared across the API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Returned after a successful PDF upload & embedding."""

    filename: str
    num_chunks: int
    collection_name: str
    conversation_id: str
    message: str = "PDF processed successfully"


# ── Query ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Incoming question from the user."""

    question: str
    conversation_id: str
    collection_name: str


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
    pdf_name: str
    collection_name: str
    created_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation including messages."""

    id: str
    title: str
    pdf_name: str
    collection_name: str
    created_at: datetime
    messages: list[MessageOut] = Field(default_factory=list)
