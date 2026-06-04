"""Application settings loaded from environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the PDF Wizard backend."""

    # --- Google / Gemini ---
    google_api_key: str = ""

    # --- Local Hugging Face models ---
    llm_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # --- Chunking ---
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # --- Storage paths (relative to backend/) ---
    chroma_persist_dir: str = str(Path(__file__).resolve().parent.parent / "chroma_data")
    sqlite_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'pdf_wizard.db'}"

    # --- Upload ---
    max_upload_bytes: int = 20 * 1024 * 1024  # 20 MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
