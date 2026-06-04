"""Extract text from uploaded PDF files."""

from __future__ import annotations

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text(file_bytes: bytes) -> str:
    """Read every page of a PDF and return the concatenated text.

    Args:
        file_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        The full extracted text as a single string.

    Raises:
        ValueError: If the PDF contains no extractable text.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text: list[str] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text)
        logger.debug("Page %d: extracted %d chars", i + 1, len(text))

    full_text = "\n\n".join(pages_text)

    if not full_text.strip():
        raise ValueError(
            "The uploaded PDF contains no extractable text. "
            "It may be scanned / image-only."
        )

    logger.info(
        "Extracted %d chars across %d pages",
        len(full_text),
        len(reader.pages),
    )
    return full_text
