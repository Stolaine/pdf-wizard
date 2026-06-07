from __future__ import annotations

import logging
import os
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    question: str
    collection_names: list[str]
    context: list[dict]
    answer: str
    thinking: str
    sources: list[Document]


def embed_node(state: AgentState) -> dict:
    """Invokes embed_pdf tool to ingest a PDF from a filepath."""
    logger.info("Agent: entering embed_node")
    question = state["question"]
    
    # Extract file path candidates from the user's message
    words = question.split()
    file_path = None
    for w in words:
        w_clean = w.strip('`"\'')
        if w_clean.lower().endswith(".pdf"):
            file_path = w_clean
            break
            
    if not file_path:
        file_path = question.strip('`"\'')

    from app.tools.pdf_tools import embed_pdf
    try:
        res = embed_pdf.invoke({"file_path": file_path})
        if res["status"] == "success":
            return {
                "answer": f"Successfully embedded {res['filename']}! Ingested {res['num_chunks']} chunks into collection '{res['collection_name']}'.",
                "thinking": "Detected filepath query and processed it using the embed_pdf tool successfully.",
                "sources": [],
            }
        else:
            return {
                "answer": f"Failed to embed PDF: {res['message']}",
                "thinking": f"Attempted to call embed_pdf on '{file_path}' but it returned an error.",
                "sources": [],
            }
    except Exception as exc:
        logger.exception("Agent: failed to invoke embed_pdf tool")
        return {
            "answer": f"An error occurred while embedding the file: {exc}",
            "thinking": f"Exception raised when calling embed_pdf tool: {exc}",
            "sources": [],
        }


def retrieve_node(state: AgentState) -> dict:
    """Invokes extract_similar_vector tool to retrieve context documents."""
    logger.info("Agent: entering retrieve_node")
    query = state["question"]
    cols = state["collection_names"]
    
    if not cols:
        return {
            "context": [],
            "answer": "No document context is linked to this chat yet. Please upload or add a PDF first!",
            "thinking": "Collections list is empty; skipped retrieval.",
            "sources": [],
        }

    from app.tools.pdf_tools import extract_similar_vector
    try:
        chunks = extract_similar_vector.invoke({"query": query, "collection_names": cols})
        return {"context": chunks}
    except Exception as exc:
        logger.exception("Agent: failed to invoke extract_similar_vector tool")
        return {
            "context": [],
            "answer": f"Failed to retrieve document search results: {exc}",
            "thinking": f"Exception raised when calling extract_similar_vector tool: {exc}",
            "sources": [],
        }


def generate_node(state: AgentState) -> dict:
    """Invokes generate_response tool to construct the final LLM response based on context."""
    logger.info("Agent: entering generate_node")
    # If retrieve_node set an answer (like for empty collections), skip generation
    if state.get("answer"):
        return {}

    query = state["question"]
    context = state.get("context", [])

    from app.tools.pdf_tools import generate_response
    try:
        res = generate_response.invoke({"query": query, "retrieved_context": context})
        return {
            "answer": res["answer"],
            "thinking": res["thinking"],
            "sources": res["source_documents"],
        }
    except Exception as exc:
        logger.exception("Agent: failed to invoke generate_response tool")
        return {
            "answer": f"Failed to construct LLM response: {exc}",
            "thinking": f"Exception raised when calling generate_response tool: {exc}",
            "sources": [],
        }


# ── LangGraph Workflow Construction ─────────────────────────────────────────

workflow = StateGraph(AgentState)

# Register nodes
workflow.add_node("embed", embed_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)


# Define entry condition
def route_start(state: AgentState) -> str:
    question = state["question"].strip()
    is_embed = False
    
    # Check if this query is a command/request to embed a PDF
    if question.lower().endswith(".pdf") or "embed" in question.lower() or "ingest" in question.lower():
        words = question.split()
        for w in words:
            w_clean = w.strip('`"\'')
            if w_clean.lower().endswith(".pdf"):
                is_embed = True
                break
                
    if is_embed:
        return "embed"
    return "retrieve"


workflow.set_conditional_entry_point(
    route_start,
    {
        "embed": "embed",
        "retrieve": "retrieve",
    }
)

# Connect edges
workflow.add_edge("embed", END)
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# Compile the agent app
agent_app = workflow.compile()


def run_agent(question: str, collection_names: list[str]) -> dict:
    """Execute the compiled LangGraph agent graph with the user's question and context."""
    logger.info("Running LangGraph agent for question: '%s'", question)
    
    initial_state = AgentState(
        question=question,
        collection_names=collection_names,
        context=[],
        answer="",
        thinking="",
        sources=[],
    )
    
    try:
        final_state = agent_app.invoke(initial_state)
        return {
            "answer": final_state.get("answer", ""),
            "thinking": final_state.get("thinking", ""),
            "source_documents": final_state.get("sources", []),
        }
    except Exception as exc:
        logger.exception("LangGraph agent execution failed")
        raise exc
