# NoteWork - Open NotebookLM

[中文文档](./README.zh-CN.md)

NoteWork is an AI research workspace built with Vue 3 and FastAPI. It
organizes content around notebooks, lets users upload or link sources, chats
with retrieval grounding and citations, and generates studio artifacts such as
mind maps, slide decks, infographics, reports, and deep research briefs.

## Current Capabilities

- **Notebook-centric workspace** for collecting sources, chats, notes, and
  generated assets.
- **Source ingestion from URLs or file uploads** with support for `pdf`,
  `docx`, `doc`, `txt`, `md`, `csv`, `pptx`, images, audio, and video.
- **Multimodal preprocessing**:
  - images are summarized with vision models
  - audio is transcribed with Qwen ASR, including long-audio fallback
  - video is summarized with Qwen VL
- **Grounded chat with citations** plus SSE streaming for search steps and
  final answers.
- **Studio generation** for mind maps, slide decks, infographics, reports, and
  Deep Research tasks.
- **User notes and settings**, including model selection controls for paid
  users.
- **JWT auth + OAuth login** for Google, Weibo, QQ, and Alipay.
- **Subscription and payments** with Alipay and WeChat Pay QR code flows.
- **Async task processing** with Celery plus SSE task-status streaming.
- **Object storage integration** with Alibaba Cloud OSS.
- **Tracing and optional external integrations** including Langfuse and
  DeerFlow.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | Vue 3, Vite, TypeScript, Vuetify, Pinia, Vue Router, Vue I18n, Axios |
| Backend | FastAPI, SQLAlchemy async, Pydantic Settings, Alembic |
| App Data | MySQL via `aiomysql` |
| Vector Search | Milvus |
| Queue / Realtime | Celery, Redis, SSE |
| AI | LiteLLM, DashScope / Qwen3-Max, Qwen3-VL, Qwen ASR |
| Storage | Alibaba Cloud OSS |
| Infra | Docker, Nginx |

## Architecture At A Glance

1. The frontend calls FastAPI APIs for notebooks, sources, chat, notes,
   settings, payments, and studio generation.
2. Uploaded files are stored in object storage; parsed content and notebook
   metadata are stored in the application database.
3. Vector data is stored in Milvus rather than in the relational database.
4. Long-running source and studio jobs are dispatched to Celery and streamed
   back to the UI through task-event SSE endpoints.
5. Deep Research is an optional integration that calls a separately deployed
   DeerFlow gateway.

## Repository Layout

```text
notebookLM/
├── frontend/                    # Vue 3 + Vite application
│   ├── src/api/                 # HTTP clients
│   ├── src/components/          # Source/chat/studio/payment UI
│   ├── src/stores/              # Pinia stores
│   ├── src/views/               # Landing, home, notebook, login, pricing, settings
│   └── src/router/              # Route definitions
├── backend/
│   ├── app/api/                 # FastAPI route modules
│   ├── app/ai/                  # LLM, vision, ASR, retrieval integrations
│   ├── app/models/              # SQLAlchemy models
│   ├── app/services/            # Business logic
│   ├── app/tasks/               # Celery tasks
│   ├── alembic/                 # DB migrations
│   └── docs/                    # Backend feature notes
├── backend.sh                   # Local FastAPI (sources optional backend-env.sh)
├── backend-celery.sh            # Local Celery worker
├── frontend.sh                  # Local Vite dev server
├── backend-env.sh               # Optional local env overrides (Redis, DB, Milvus, …)
├── makefile                     # Unified entrypoint for deploy/dev commands
├── deploy/
│   ├── middleware/              # Middleware compose + deploy-middleware.sh
│   └── ha/                      # App HA compose + deploy-app-ha.sh
├── nginx/                       # Reverse proxy configs
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11 recommended
- A reachable MySQL instance configured through `DATABASE_URL`
- Access to required model and object-storage credentials

## Quick Start

### 1. Configure the environment

```bash
cp .env.example .env
```

At minimum, review and set these values:

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND_URL`
- `TASK_EVENT_REDIS_URL`
- `MILVUS_URI`
- `QWEN_API_KEY` or compatible DashScope credentials
- `OSS_*` (including optional `OSS_PATH_PREFIX`)
- `CORS_ORIGINS`

Optional integrations:

- `DEER_FLOW_BASE_URL` for Deep Research
- `LANGFUSE_*` for traces
- `GOOGLE_OAUTH_*`, `WEIBO_OAUTH_*`, `QQ_OAUTH_*`, `ALIPAY_*`
- WeChat / Alipay payment callback settings

> `deploy/middleware/docker-compose-middleware.yml` still contains a `postgres` service,
> but the application runtime is currently configured around `DATABASE_URL`
> and the default dependency set uses MySQL via `aiomysql`. Vector retrieval
> is handled by Milvus.

### 2. Deploy with Docker (recommended Make targets)

Container deployment is split into **middleware** and **application** steps.

**Middleware** (Redis, Milvus, etcd, MinIO, Attu, and related services):

```bash
make up-middleware
```

Run this from the repository root. This target wraps
`deploy/middleware/deploy-middleware.sh`, which uses
`deploy/middleware/docker-compose-middleware.yml`, syncs the repo to
`origin/master`, then rebuilds and starts the stack. Set `NO_CACHE=true` for a
no-cache image build.

**Application** (backend, frontend, Nginx, Celery workers in HA compose files):

```bash
make up-ha
```

Requires a project-root `config.yaml` (for example copy from
`config.yaml.example`) and `.env`. Uses `deploy/ha/docker-compose.app-ha.yml`
and `deploy/ha/docker-compose.workers-ha.yml`, syncs to `origin/master`, builds
`backend` and `frontend` images, then brings the stack up. Optional:
`NO_CACHE=true`, `DEPLOY_DIR` for a non-default repo root.

For manual composition or older layouts, Compose files also live under
`deploy/` (for example `docker-compose-core.yml`). For HA and worker scaling
details, see `docs/production-scaling-blueprint.md`.

Useful endpoints after startup:

- App: `http://localhost`
- Frontend dev server: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Health checks: `http://localhost:8000/api/health/live`,
  `http://localhost:8000/api/health/ready`
- Attu for Milvus inspection: `http://localhost:8080`

## Local Development

If you want to run the frontend and backend directly on your machine while
keeping middleware in Docker:

### 1. Start middleware only

```bash
docker compose -f deploy/middleware/docker-compose-middleware.yml up -d redis milvus attu
```

Or use the full middleware script when you want the same stack as server deploy
(note: it resets the working tree to `origin/master`):

```bash
bash deploy/middleware/deploy-middleware.sh
```

Make sure `DATABASE_URL` points to a reachable MySQL instance before starting
the backend.

### 2. One-time backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 3. Run the backend, Celery worker, and frontend (repo root)

From the **repository root**, after `.env` (and optionally `backend-env.sh`) is
configured:

```bash
make dev
```

In another terminal:

```bash
make dev-celery
```

And for the Vite dev server:

```bash
make dev-frontend
```

These Make targets wrap `backend.sh`, `backend-celery.sh`, and `frontend.sh`.
`backend.sh` and `backend-celery.sh` activate `backend/.venv` when present,
`cd` into `backend`, and source optional `backend-env.sh` at the repo root for
local overrides (for example Redis and MySQL URLs pointing at `127.0.0.1` or a
remote host). `frontend.sh` runs `npm run dev` from `frontend/` (run
`npm install` there first).

Install **`yt-dlp`** on the Celery worker host (`pip install -r requirements.txt`
also installs the `yt-dlp` package; the backend uses the CLI on `PATH` or
`python -m yt_dlp`).

**Bilibili subtitles** often require a logged-in session. Export Netscape-format
cookies for `bilibili.com` (see
[yt-dlp cookies FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)),
then set **`YTDLP_COOKIES_FILE`** in `.env` or `backend-env.sh` to the absolute
path of that file and restart the Celery worker.

Equivalent manual commands (if you prefer not to use the scripts):

```bash
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd backend && source .venv/bin/activate
celery -A app.tasks.celery_app:celery_app worker --loglevel=info
```

```bash
cd frontend && npm run dev
```

## Product Limits

The current role limits in code are:

| Role | Notebooks | Sources per notebook | Daily chats |
| --- | --- | --- | --- |
| `free` | 20 | 30 | 50 |
| `paid` | 200 | 50 | 200 |
| `admin` | 200 | 50 | 9999 |

The pricing UI currently advertises paid subscription flows through Alipay and
WeChat Pay.

## API Overview

Representative endpoints:

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| OAuth | `/api/auth/oauth/{provider}/start`, `/api/auth/oauth/{provider}/callback` |
| Settings | `GET /api/settings`, `PATCH /api/settings` |
| Notebooks | `GET /api/notebooks`, `POST /api/notebooks`, `GET/PUT/DELETE /api/notebooks/{notebook_id}` |
| Sources | `POST /api/notebooks/{notebook_id}/sources`, `POST /api/notebooks/{notebook_id}/sources/upload`, `GET /api/notebooks/{notebook_id}/sources` |
| Chat | `POST /api/notebooks/{notebook_id}/chat/sessions`, `POST /api/chat/{session_id}/messages`, `POST /api/chat/{session_id}/messages/stream`, `GET /api/chat/{session_id}/messages` |
| Notes | Notebook-scoped note CRUD under `/api/notebooks/{notebook_id}/notes` |
| Studio | Mind maps, slides, infographics, and reports under notebook-scoped studio endpoints |
| Deep Research | `POST /api/notebooks/{notebook_id}/deep-research`, `GET /api/notebooks/{notebook_id}/deep-research`, `GET /api/deep-research/{report_id}` |
| Task Events | `GET /api/task-events/{resource_type}/{resource_id}/stream` |
| Payments | `POST /api/payment/create`, `GET /api/payment/status/{order_id}` |
| Health | `GET /api/health`, `GET /api/health/live`, `GET /api/health/ready` |

## Operational Notes

- Source files are stored in object storage; generated slide and infographic
  assets are also served from storage through signed URLs or proxy endpoints.
- Source parsing and studio generation are asynchronous. The frontend should
  either poll resource endpoints or subscribe to task-event SSE streams.
- Deep Research requires a separate DeerFlow deployment. See
  `backend/docs/DEEP_RESEARCH_DEERFLOW.md` for setup details.
- The backend also initializes tables on startup, but running
  `alembic upgrade head` is still recommended for keeping schema changes in
  sync.

## License

MIT
