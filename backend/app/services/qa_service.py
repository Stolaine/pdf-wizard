from __future__ import annotations

import logging

from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from app.config import settings
from app.services.vector_service import get_vectorstore

logger = logging.getLogger(__name__)

# ── LLM singleton ──────────────────────────────────────────────────────────

_llm: HuggingFacePipeline | None = None


def _get_llm() -> HuggingFacePipeline:
    global _llm
    if _llm is None:
        model_id = settings.llm_model
        logger.info("Loading local Hugging Face LLM model '%s' via transformers...", model_id)

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.3,
            do_sample=True,
        )
        _llm = HuggingFacePipeline(pipeline=pipe)
        logger.info("Local Hugging Face LLM loaded successfully.")
    return _llm


# ── Answer a question ──────────────────────────────────────────────────────

def answer_question(question: str, collection_name: str) -> dict:
    """Run a retrieval-augmented QA chain and return the result.

    Returns:
        dict with keys ``answer`` (str) and ``source_documents`` (list[Document]).
    """
    logger.info("Starting QA process for question: '%s'", question)

    # 1. Retrieve relevant chunks
    logger.info("Retrieving similar chunks from Chroma collection '%s'...", collection_name)
    vectorstore = get_vectorstore(collection_name)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    docs = retriever.invoke(question)

    logger.info("Retrieved %d relevant context chunks:", len(docs))
    for idx, doc in enumerate(docs, 1):
        snippet = doc.page_content.replace("\n", " ")[:120] + "..."
        logger.info("  [Chunk %d] Metadata: %s | Snippet: %s", idx, doc.metadata, snippet)

    # 2. Run RetrievalQA Chain
    logger.info("Sending query and retrieved context to Hugging Face LLM (%s)...", settings.llm_model)

    qa_chain = RetrievalQA.from_chain_type(
        llm=_get_llm(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )

    result = qa_chain.invoke({"query": question})
    raw_output = result["result"]
    logger.info("Successfully generated answer from Hugging Face LLM (length=%d).", len(raw_output))

    # Parse raw output into thinking and helpful answer
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

    logger.info("Parsed Thinking (length=%d):\n%s", len(thinking), thinking)
    logger.info("Parsed Helpful Answer (length=%d):\n%s", len(helpful_answer), helpful_answer)

    return {
        "answer": helpful_answer,
        "thinking": thinking,
        "source_documents": result.get("source_documents", []),
    }
