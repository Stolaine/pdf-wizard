from __future__ import annotations

import logging

from langchain.chains.question_answering import load_qa_chain
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

def answer_question(question: str, collection_names: list[str]) -> dict:
    """Run a retrieval-augmented QA chain across multiple Chroma collections and return the result.

    Returns:
        dict with keys ``answer``, ``thinking``, and ``source_documents``.
    """
    logger.info("Starting multi-file QA process for question: '%s'", question)

    # 1. Retrieve relevant chunks from all collections
    all_docs = []
    for col_name in collection_names:
        try:
            logger.info("Retrieving similar chunks from Chroma collection '%s'...", col_name)
            vectorstore = get_vectorstore(col_name)
            docs = vectorstore.similarity_search(question, k=3)
            all_docs.extend(docs)
        except Exception as exc:
            logger.warning("Failed to retrieve from collection '%s': %s", col_name, exc)

    logger.info("Retrieved %d total relevant context chunks across all collections:", len(all_docs))
    for idx, doc in enumerate(all_docs, 1):
        snippet = doc.page_content.replace("\n", " ")[:120] + "..."
        logger.info("  [Chunk %d] Metadata: %s | Snippet: %s", idx, doc.metadata, snippet)

    # 2. Run QA Stuff Chain manually
    logger.info("Sending query and retrieved context to Hugging Face LLM (%s)...", settings.llm_model)

    qa_chain = load_qa_chain(
        llm=_get_llm(),
        chain_type="stuff",
    )

    result = qa_chain.invoke({"input_documents": all_docs, "question": question})
    raw_output = result["output_text"]
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
        "source_documents": all_docs,
    }
