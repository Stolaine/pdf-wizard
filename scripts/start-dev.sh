#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start-dev.sh — Run backend and frontend as SEPARATE processes (dev mode)
#
# Backend:  http://localhost:8000  (FastAPI with hot-reload)
# Frontend: http://localhost:5173  (Vite dev server, proxies /api to backend)
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting PDF Wizard in DEV mode..."
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""

# ── Start backend ───────────────────────────────────────────────────────────
echo "📦 Starting backend..."
(
  cd "$ROOT_DIR/backend"
  if [ -d "$ROOT_DIR/.venv" ]; then
    echo "   Using root virtual environment..."
    source "$ROOT_DIR/.venv/bin/activate"
  elif [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    echo "   Creating virtual environment in backend..."
    python3 -m venv .venv
    source .venv/bin/activate
  fi
  pip install -q -r requirements.txt
  uvicorn app.main:app --reload --port 8000
) &

# ── Start frontend ──────────────────────────────────────────────────────────
echo "🎨 Starting frontend..."
(
  cd "$ROOT_DIR/frontend"
  if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
  fi
  npm run dev
) &
FRONTEND_PID=$!

# ── Cleanup on exit ────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "🛑 Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "✅ Done."
}
trap cleanup EXIT INT TERM

# Wait for both
wait
