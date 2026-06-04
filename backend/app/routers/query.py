"""Query router — handles user questions against uploaded PDFs."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import QueryRequest, QueryResponse, SourceChunk
from app.services import qa_service, history_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_pdf(
    body: QueryRequest,
    db: Session = Depends(get_db),
):
    """Ask a question about an uploaded PDF and get an answer."""

    # Verify conversation exists
    conversation = history_service.get_conversation(db, body.conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Save user question
    history_service.add_message(db, body.conversation_id, "user", body.question)

    # Get answer from QA chain
    try:
        result = qa_service.answer_question(body.question, body.collection_name)
    except Exception as exc:
        logger.exception("QA chain failed")
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {exc}")

    answer = result["answer"]
    source_docs = result.get("source_documents", [])

    # Save assistant answer
    history_service.add_message(db, body.conversation_id, "assistant", answer)

    # Build source snippets
    sources = [
        SourceChunk(
            content=doc.page_content[:300],
            page=doc.metadata.get("page"),
        )
        for doc in source_docs
    ]

    return QueryResponse(
        answer=answer,
        conversation_id=body.conversation_id,
        sources=sources,
    )
