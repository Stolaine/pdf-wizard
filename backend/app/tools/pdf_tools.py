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


@tool
def extract_similar_vector(query: str, collection_names: list[str]) -> list[dict]:
    """Retrieves context chunks most similar to a query from specified vector collections.

    Args:
        query: The semantic search query phrase.
        collection_names: The names of the ChromaDB collections to search.

    Returns:
        A list of dictionaries containing keys:
        - page_content: The text content of the chunk.
        - page: The page number within the original document (if available).
    """
    logger.info("Tool extract_similar_vector called for query: '%s' in collections: %s", query, collection_names)
    all_chunks = []
    
    for col_name in collection_names:
        try:
            vectorstore = vector_service.get_vectorstore(col_name)
            docs = vectorstore.similarity_search(query, k=3)
            for doc in docs:
                all_chunks.append({
                    "page_content": doc.page_content,
                    "page": doc.metadata.get("page"),
                })
        except Exception as exc:
            logger.warning("Failed to search collection '%s': %s", col_name, exc)

    logger.info("Tool extract_similar_vector retrieved %d matching chunks", len(all_chunks))
    return all_chunks


@tool
def generate_response(query: str, retrieved_context: list[dict]) -> dict:
    """Uses LLM text generation to build a helpful answer for the user query based on context.

    Args:
        query: The user's query question.
        retrieved_context: List of context dictionaries (with content and page details).

    Returns:
        A dictionary containing:
        - answer: The final helpful answer.
        - thinking: The parsed chain-of-thought/reasoning output of the LLM.
        - source_documents: Reconstructed document fragments used in answering.
    """
    logger.info("Tool generate_response called for query: '%s' with %d context chunks", query, len(retrieved_context))
    
    # 1. Convert back to LangChain Documents for QA Chain compatibility
    from langchain_core.documents import Document
    lc_docs = [
        Document(page_content=c["page_content"], metadata={"page": c["page"]})
        for c in retrieved_context
    ]

    # 2. Invoke local HF pipeline QA stuff chain
    from app.services import qa_service
    from langchain.chains.question_answering import load_qa_chain
    
    qa_chain = load_qa_chain(
        llm=qa_service._get_llm(),
        chain_type="stuff",
    )

    result = qa_chain.invoke({"input_documents": lc_docs, "question": query})
    raw_output = result["output_text"]

    helpful_answer = raw_output
    thinking = ""

    question_marker = "Question:"
    helpful_answer_marker = "Helpful Answer:"

    q_idx = raw_output.find(question_marker)
    a_idx = raw_output.find(helpful_answer_marker)

    if a_idx != -1:
        helpful_answer = raw_output[a_idx + len(helpful_answer_marker):].strip()
        if q_idx != -1 and q_idx < a_idx:
            thinking = raw_output[:q_idx].strip()
        else:
            thinking = raw_output[:a_idx].strip()
    else:
        if q_idx != -1:
            thinking = raw_output[:q_idx].strip()
            helpful_answer = raw_output[q_idx + len(question_marker):].strip()

    return {
        "answer": helpful_answer,
        "thinking": thinking,
        "source_documents": lc_docs,
    }
