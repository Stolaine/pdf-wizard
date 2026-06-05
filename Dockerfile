# ── Build stage: frontend ───────────────────────────────────────────────────
FROM node:22-alpine AS frontend-build

WORKDIR /build

# Install deps first (cached layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build


# ── Runtime stage: backend + built frontend ────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# System deps for chromadb (needs build tools for some native extensions)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps (cached layer)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download local Hugging Face models so they are cached inside the image
RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct'); AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Copy backend source
COPY backend/app ./app

# Copy built frontend into /app/static
COPY --from=frontend-build /build/dist ./static

# Create data directory for DBs (SQLite + ChromaDB)
RUN mkdir -p /app/data

# Set environment variables for data paths
ENV CHROMA_PERSIST_DIR=/app/data/chroma_data
ENV SQLITE_URL=sqlite:////app/data/pdf_wizard.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
