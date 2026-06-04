"""Chunking, embedding, and ChromaDB vector operations."""

from __future__ import annotations

import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

# ── Shared embedding function ──────────────────────────────────────────────

_embeddings: GoogleGenerativeAIEmbeddings | None = None


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Lazily initialise the Google embedding model."""
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
        )
    return _embeddings


# ── Chunking ────────────────────────────────────────────────────────────────

def chunk_text(text: str) -> list[Document]:
    """Split text into overlapping chunks suitable for embedding.

    Returns a list of LangChain Document objects, each with page_content set.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.create_documents([text])
    logger.info("Created %d chunks (size=%d, overlap=%d)", len(docs), settings.chunk_size, settings.chunk_overlap)
    return docs


# ── Store ───────────────────────────────────────────────────────────────────

def store_embeddings(documents: list[Document], collection_name: str) -> Chroma:
    """Embed documents and persist them in ChromaDB under *collection_name*.

    Returns the Chroma vectorstore handle (useful for immediate querying).
    """
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=_get_embeddings(),
        collection_name=collection_name,
        persist_directory=settings.chroma_persist_dir,
    )
    logger.info("Stored %d documents in collection '%s'", len(documents), collection_name)
    return vectorstore


# ── Retrieve ────────────────────────────────────────────────────────────────

def get_vectorstore(collection_name: str) -> Chroma:
    """Return an existing Chroma vectorstore for *collection_name*."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=_get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


def search_similar(query: str, collection_name: str, k: int = 5) -> list[Document]:
    """Retrieve the *k* most similar chunks to *query*."""
    vs = get_vectorstore(collection_name)
    results = vs.similarity_search(query, k=k)
    logger.info("Found %d similar chunks for query in '%s'", len(results), collection_name)
    return results
