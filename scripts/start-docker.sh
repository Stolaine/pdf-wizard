#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start-docker.sh — Build and run the app in Docker
#
# App: http://localhost:8000  (single container, API + frontend)
#
# Usage:
#   ./scripts/start-docker.sh          # Build & run
#   ./scripts/start-docker.sh --build  # Force rebuild
#   ./scripts/start-docker.sh --down   # Stop & remove
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

# ── Check .env exists ──────────────────────────────────────────────────────
if [ ! -f "backend/.env" ]; then
  echo "❌ backend/.env not found!"
  echo "   Create it with your GOOGLE_API_KEY:"
  echo "   echo 'GOOGLE_API_KEY=your-key-here' > backend/.env"
  exit 1
fi

# ── Handle flags ───────────────────────────────────────────────────────────
case "${1:-}" in
  --down)
    echo "🛑 Stopping PDF Wizard..."
    docker compose down
    echo "✅ Stopped."
    exit 0
    ;;
  --build)
    echo "🔨 Force rebuilding..."
    docker compose build --no-cache
    ;;
esac

# ── Start ──────────────────────────────────────────────────────────────────
echo "🚀 Starting PDF Wizard in Docker..."
echo "   App: http://localhost:8000"
echo ""
docker compose up --build -d
echo ""
echo "✅ PDF Wizard is running!"
echo "   Open http://localhost:8000"
echo "   Logs: docker compose logs -f"
echo "   Stop: ./scripts/start-docker.sh --down"
