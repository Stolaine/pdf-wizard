#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start-local.sh — Build frontend & run as a SINGLE local application
#
# App: http://localhost:8000  (FastAPI serves both API + built frontend)
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting PDF Wizard in SINGLE-APP mode..."
echo ""

# ── Build frontend ──────────────────────────────────────────────────────────
echo "🎨 Building frontend..."
(
  cd "$ROOT_DIR/frontend"
  if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
  fi
  npm run build
)
echo "✅ Frontend built → frontend/dist/"
echo ""

# ── Start backend (serves built frontend) ──────────────────────────────────
echo "📦 Starting backend..."
(
  cd "$ROOT_DIR/backend"
  if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install -q -r requirements.txt
  echo ""
  echo "✅ App running at http://localhost:8000"
  echo ""
  uvicorn app.main:app --host 0.0.0.0 --port 8000
)
