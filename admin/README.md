# Admin Dashboard

Standalone admin dashboard for NotebookLM — independently deployable, connects to the shared MySQL database.

## Structure

```
admin/
├── backend/          # FastAPI admin API (Python)
│   ├── app/
│   │   ├── api/      # auth.py, admin.py, deps.py
│   │   ├── schemas/  # Pydantic request/response models
│   │   └── services/ # Business logic
│   ├── Dockerfile
│   ├── config.yaml   # Copy from backend/config.yaml, adjust as needed
│   └── .env          # Secret keys (copy from .env.example)
├── frontend/         # Vue 3 + Vite admin UI
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

## Prerequisites

- Docker and Docker Compose
- The main project's `notebooklm_default` Docker network must exist:
  ```bash
  docker network create notebooklm_default
  # Or it is created automatically when running the main project's docker-compose
  ```

## Setup

### 1. Configure the backend

```bash
# Copy and edit the environment file
cp admin/backend/.env.example admin/backend/.env
# Edit admin/backend/.env — set SECRET_KEY and any other secrets

# Copy and edit the config file (same database settings as the main backend)
cp backend/config.yaml admin/backend/config.yaml
# Edit admin/backend/config.yaml if needed
```

### 2. Build and start

Run from the **repo root** (required so Docker can access both `shared/` and `admin/`):

```bash
docker compose -f admin/docker-compose.yml up --build -d
```

The admin UI will be available at **http://localhost:8080**.

## Usage

1. Open http://localhost:8080
2. Log in with an admin-role account
3. Manage users, featured notebooks, and system settings

## Development

### Backend

```bash
cd admin/backend
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd admin/frontend
npm install
npm run dev   # dev server on http://localhost:5173
```

Set `VITE_API_BASE` or configure the Vite proxy in `vite.config.ts` to point to the running backend.
