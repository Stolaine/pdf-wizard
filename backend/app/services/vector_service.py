"""Chunking, embedding, and ChromaDB vector operations."""

from __future__ import annotations

import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

# ── Shared embedding function ──────────────────────────────────────────────

_embeddings: HuggingFaceEmbeddings | None = None


def _get_embeddings() -> HuggingFaceEmbeddings:
    """Lazily initialise the local HuggingFace embedding model."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
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
    """Embed documents and persist them in ChromaDB in batches with progress logging.

    Returns the Chroma vectorstore handle.
    """
    embeddings_impl = _get_embeddings()
    batch_size = 20
    total_docs = len(documents)

    logger.info("Starting embedding generation for %d chunks in batches of %d...", total_docs, batch_size)

    vectorstore = None
    for i in range(0, total_docs, batch_size):
        batch = documents[i : i + batch_size]
        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings_impl,
                collection_name=collection_name,
                persist_directory=settings.chroma_persist_dir,
            )
        else:
            vectorstore.add_documents(batch)

        processed = min(i + batch_size, total_docs)
        percent = (processed / total_docs) * 100
        logger.info("Embedded and stored %d/%d chunks (%.1f%% complete)", processed, total_docs, percent)

    logger.info("Successfully finished embedding storage for collection '%s'", collection_name)
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
