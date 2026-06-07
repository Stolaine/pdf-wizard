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
    """Ask a question about the conversation's linked PDF contexts and get an answer."""

    # Verify conversation exists
    conversation = history_service.get_conversation(db, body.conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # Save user question
    history_service.add_message(db, body.conversation_id, "user", body.question)

    # Resolve linked context files and collection names
    collection_names = [f.collection_name for f in conversation.files]

    if not collection_names:
        logger.info("No file context linked to conversation '%s'", conversation.id)
        answer = "No document context is linked to this chat yet. Please upload or add a PDF first!"
        history_service.add_message(db, body.conversation_id, "assistant", answer)
        return QueryResponse(
            answer=answer,
            thinking="No file context present.",
            conversation_id=body.conversation_id,
            sources=[],
        )

    # Prevent querying if any linked file is still embedding
    non_completed_files = [f for f in conversation.files if f.status in ("PENDING", "PROCESSING")]
    if non_completed_files:
        filenames = ", ".join([f"'{f.filename}'" for f in non_completed_files])
        answer = f"Please wait! The following file(s) are still being processed: {filenames}. You can start querying once embedding is complete."
        history_service.add_message(db, body.conversation_id, "assistant", answer, thinking="Embedding in progress.")
        return QueryResponse(
            answer=answer,
            thinking="Embedding in progress.",
            conversation_id=body.conversation_id,
            sources=[],
        )

    # Get answer from LangGraph agent
    try:
        from app.services import agent_service
        result = agent_service.run_agent(body.question, collection_names)
    except Exception as exc:
        logger.exception("LangGraph agent execution failed")
        raise HTTPException(status_code=500, detail=f"Failed to generate answer via agent: {exc}")

    answer = result["answer"]
    thinking = result.get("thinking", "")
    source_docs = result.get("source_documents", [])

    # Save assistant answer
    history_service.add_message(db, body.conversation_id, "assistant", answer, thinking=thinking)

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
        thinking=thinking,
        conversation_id=body.conversation_id,
        sources=sources,
    )

