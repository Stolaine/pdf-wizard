"""PDF Wizard — FastAPI application entry-point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db
from app.routers import history, query, upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# Possible locations for the built frontend
_STATIC_CANDIDATES = [
    Path("/app/static"),                                    # Docker
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",  # Local single-app
]


def _find_static_dir() -> Path | None:
    """Return the first existing static directory, or None."""
    for candidate in _STATIC_CANDIDATES:
        if candidate.is_dir() and (candidate / "index.html").exists():
            return candidate
    return None


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

# CORS – allow the Vite dev server (only needed in dev mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(history.router)


@app.get("/api/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}


# ── Serve built frontend (production / single-app mode) ────────────────────

_static_dir = _find_static_dir()

if _static_dir:
    logger.info("Serving frontend from %s", _static_dir)

    # Serve static assets (js, css, images, etc.)
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    # Catch-all: serve index.html for any non-API route (SPA client-side routing)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA – return index.html for all non-API, non-asset paths."""
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_static_dir / "index.html")
else:
    logger.info("No built frontend found — running in API-only mode (use Vite dev server)")

