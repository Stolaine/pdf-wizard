"""PDF Wizard — FastAPI application entry-point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.routers import history, query, upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run once on startup: initialise the database."""
    logger.info("Initialising database …")
    init_db()
    logger.info("Database ready ✓")
    yield  # app runs here
    logger.info("Shutting down …")


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PDF Wizard API",
    description="RAG-powered PDF question-answering backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(history.router)


@app.get("/api/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}
