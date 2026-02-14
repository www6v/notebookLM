# NotebookLM Clone

An AI-powered research tool inspired by Google NotebookLM. Upload sources (PDF, web pages, YouTube videos, etc.), then interact with an AI that answers questions grounded in those sources — with citations, mind maps, slide decks, infographics, and more.

## Tech Stack

- **Frontend**: Vue 3 + Vite + Element Plus + Pinia
- **Backend**: Python FastAPI + SQLAlchemy 2.0
- **Database**: PostgreSQL + pgvector
- **AI**: LiteLLM (multi-model: OpenAI, Anthropic, Google, Azure, Ollama)
- **Task Queue**: Celery + Redis

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)

### Using Docker (recommended)

```bash
# Start all services
docker compose up -d

# Open the app
open http://localhost:5173
```

### Local Development

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL + Redis via Docker
docker compose up -d postgres redis

# Run the backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Configuration

Copy and edit the environment file:

```bash
cp backend/.env.example backend/.env
```

Key settings:
- `SECRET_KEY` — JWT signing key (change in production)
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — Your OpenAI API key (or configure other providers)

## Features

- **Multi-format Source Management** — Upload PDF, DOCX, TXT, Markdown, or add web pages and YouTube videos
- **RAG Chat with Citations** — AI answers grounded in your sources with inline citation references
- **Notes & Pinboard** — Create, edit, pin notes; save chat responses as notes
- **Mind Map Generation** — AI-generated interactive mind maps from your sources
- **Slide Deck Generation** — AI creates structured presentations with multiple themes
- **Infographic Generation** — Template-based infographics (timeline, comparison, process, statistics, hierarchy)
- **Multi-Model Support** — Switch between OpenAI, Anthropic, Google, Azure, or local Ollama models

## Project Structure

```
notebookLM/
├── frontend/          # Vue 3 + Vite
│   ├── src/
│   │   ├── views/     # Page components
│   │   ├── components/# UI components
│   │   ├── stores/    # Pinia state management
│   │   ├── api/       # API service layer
│   │   └── router/    # Vue Router
│   └── ...
├── backend/           # FastAPI
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   ├── ai/        # LLM & RAG pipeline
│   │   ├── parsers/   # Document parsers
│   │   └── tasks/     # Celery async tasks
│   └── ...
├── docker-compose.yml
├── nginx/nginx.conf
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/login` | Login |
| GET | `/api/notebooks` | List notebooks |
| POST | `/api/notebooks` | Create notebook |
| GET/PUT/DELETE | `/api/notebooks/:id` | Notebook CRUD |
| POST | `/api/notebooks/:id/sources` | Add source |
| POST | `/api/notebooks/:id/sources/upload` | Upload file |
| GET | `/api/notebooks/:id/sources` | List sources |
| POST | `/api/notebooks/:id/chat/sessions` | Create chat |
| POST | `/api/notebooks/:id/notes` | Create note |
| POST | `/api/notebooks/:id/mindmap` | Generate mind map |
| POST | `/api/notebooks/:id/slides` | Generate slides |
| POST | `/api/notebooks/:id/infographics` | Generate infographic |

## License

MIT
