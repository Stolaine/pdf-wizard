"""Question-answering service using LangChain + Gemini."""

from __future__ import annotations

import logging

from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.services.vector_service import get_vectorstore

logger = logging.getLogger(__name__)

# ── LLM singleton ──────────────────────────────────────────────────────────

_llm: ChatGoogleGenerativeAI | None = None


def _get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
    return _llm


# ── Answer a question ──────────────────────────────────────────────────────

def answer_question(question: str, collection_name: str) -> dict:
    """Run a retrieval-augmented QA chain and return the result.

    Returns:
        dict with keys ``answer`` (str) and ``source_documents`` (list[Document]).
    """
    vectorstore = get_vectorstore(collection_name)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    qa_chain = RetrievalQA.from_chain_type(
        llm=_get_llm(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )

    result = qa_chain.invoke({"query": question})
    logger.info("Generated answer for collection '%s'", collection_name)

    return {
        "answer": result["result"],
        "source_documents": result.get("source_documents", []),
    }
