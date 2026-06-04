# PDF Wizard 🧙‍♂️

AI-powered PDF question-answering app. Upload a document, ask questions, get instant answers grounded in the PDF content.

## Tech Stack

| Layer     | Technology                               |
|-----------|------------------------------------------|
| Frontend  | React 19, Vite, Tailwind CSS v4, shadcn/ui |
| Backend   | FastAPI, Python 3.12+                     |
| LLM       | Google Gemini (via LangChain)             |
| Vectors   | ChromaDB                                 |
| History   | SQLite (via SQLAlchemy)                   |

## Prerequisites

1. **Google API Key** — Get one from [AI Studio](https://aistudio.google.com/apikey)
2. Create `backend/.env`:
   ```
   GOOGLE_API_KEY=your-key-here
   ```

---

## 🚀 Running the App

### Option 1: Docker (single container)

```bash
./scripts/start-docker.sh          # Build & start
./scripts/start-docker.sh --down   # Stop
./scripts/start-docker.sh --build  # Force rebuild
```

App runs at **http://localhost:8000**

### Option 2: Local — Single App

Builds the frontend and serves everything from the backend on one port.

```bash
./scripts/start-local.sh
```

App runs at **http://localhost:8000**

### Option 3: Local — Dev Mode (separate processes)

Runs backend and frontend as separate processes with hot-reload.

```bash
./scripts/start-dev.sh
```

- Backend: **http://localhost:8000**
- Frontend: **http://localhost:5173** ← open this one

---

## Usage

1. Click **New Chat** in the sidebar
2. Upload a PDF (drag & drop or click)
3. Ask questions in the chat input
4. Switch between past conversations in the sidebar

## Project Structure

```
pdf-wizard/
├── backend/             # FastAPI + LangChain + ChromaDB
│   ├── app/
│   │   ├── main.py      # App entry point
│   │   ├── config.py    # Settings
│   │   ├── models.py    # Pydantic schemas
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── db/          # SQLAlchemy ORM
│   ├── requirements.txt
│   └── .env             # API keys (not committed)
├── frontend/            # React + Vite + Tailwind
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/  # UI components
│   │   └── lib/         # API client + utils
│   └── package.json
├── scripts/
│   ├── start-dev.sh     # Dev mode (separate processes)
│   ├── start-local.sh   # Single app (local)
│   └── start-docker.sh  # Docker deployment
├── Dockerfile           # Multi-stage build
├── docker-compose.yml
└── .gitignore
```
