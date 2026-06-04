# PDF Wizard 🧙‍♂️

AI-powered PDF question-answering app. Upload a document, ask questions, get instant answers grounded in the PDF content.

## Tech Stack

| Layer     | Technology                               |
|-----------|------------------------------------------|
| Frontend  | React 19, Vite, Tailwind CSS v4, shadcn/ui |
| Backend   | FastAPI, Python 3.11+                     |
| LLM       | Google Gemini (via LangChain)             |
| Vectors   | ChromaDB                                 |
| History   | SQLite (via SQLAlchemy)                   |

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
GOOGLE_API_KEY=your-google-api-key
```

Run:
```bash
uvicorn app.main:app --reload
```

The API is now live at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` (Vite proxies `/api` requests to the backend).

## Usage

1. Click **New Chat** in the sidebar
2. Upload a PDF (drag & drop or click)
3. Ask questions in the chat input
4. Switch between past conversations in the sidebar
