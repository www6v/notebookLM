# NoteWorks - Open NotebookLM

[中文文档](./README.zh-CN.md)

NoteWorks is an AI research workspace built with Vue 3 and FastAPI. It
organizes content around notebooks, lets users upload or link sources, chats
with retrieval grounding and citations, and generates studio artifacts such as
mind maps, slide decks, infographics, reports, and deep research briefs.

## Current Capabilities

- **Notebook-centric workspace** for collecting sources, chats, notes, and
  generated assets.
- **Source ingestion from URLs or file uploads** with support for `pdf`,
  `docx`, `doc`, `txt`, `md`, `csv`, `pptx`, images, audio, and video.
- **Optional MinerU integration** for higher-quality PDF → Markdown parsing
  when `MINERU_API_KEY` and related settings are configured.
- **Multimodal preprocessing**:
  - images are summarized with vision models
  - audio is transcribed with Qwen ASR, including long-audio fallback
  - video is summarized with Qwen VL
- **Grounded chat with citations** via the **Deep Searcher** HTTP service
  (upload / load-files / query); long-running work uses **SSE** on task-event
  endpoints (sources, studio, and similar jobs).
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
| Retrieval / indexing | Deep Searcher (remote HTTP); embeddings via DashScope; Milvus optional in middleware compose (legacy companion) |
| Queue / Realtime | Celery, Redis, SSE |
| AI | LiteLLM router, DashScope (Qwen chat / VL / ASR / embeddings), optional OpenAI / Gemini keys |
| Storage | Alibaba Cloud OSS |
| Infra | Docker, Nginx |

## Architecture At A Glance

1. The frontend calls FastAPI APIs for notebooks, sources, chat, notes,
   settings, payments, and studio generation.
2. Uploaded files are stored in object storage; parsed content and notebook
   metadata are stored in the application database.
3. **Source indexing and chat Q&A** go through the configured **Deep Searcher**
   base URL (see `deep_searcher` in `config.yaml`). The sample
   `config.yaml.example` keeps the Milvus block commented; Milvus may still
   appear in middleware Compose for other or legacy setups.
4. Long-running source and studio jobs are dispatched to Celery and streamed
   back to the UI through task-event SSE endpoints.
5. Deep Research is an optional integration that calls a separately deployed
   DeerFlow gateway (`deer_flow` in `config.yaml`).

## Repository Layout

```text
notebookLM/
├── config.yaml.example          # Application config template (copy to config.yaml)
├── .env.example                 # Secrets for $VAR expansion in config.yaml
├── frontend/                    # Vue 3 + Vite application
│   ├── src/api/                 # HTTP clients
│   ├── src/components/          # Source/chat/studio/payment UI
│   ├── src/stores/              # Pinia stores
│   ├── src/views/               # Landing, home, notebook, login, pricing, settings
│   └── src/router/              # Route definitions
├── src-tauri/                   # Optional Tauri desktop shell (see package.json scripts)
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
├── backend-env.sh               # Optional local env overrides (Redis, DB, …)
├── makefile                     # make install / dev / up-middleware / up-ha
├── deploy/
│   ├── core/                    # Core compose helpers
│   ├── middleware/              # Middleware compose + deploy-middleware.sh
│   └── ha/                      # App HA compose + deploy-app-ha.sh
├── nginx/                       # Reverse proxy configs
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.11 recommended ([uv](https://github.com/astral-sh/uv) optional; `make install` uses `uv sync`)
- A reachable MySQL instance (referenced from `config.yaml` → `database.url`, usually via `DATABASE_URL` in `.env`)
- A running **Deep Searcher** compatible service for source indexing and chat (`deep_searcher.deep_searcher_base_url`)
- Access to required model and object-storage credentials

## Quick Start

### 1. Configure `config.yaml` and `.env`

The backend loads **`config.yaml`** at the repo root (override with
`NOTEBOOKLM_CONFIG_PATH`). The **`.env`** file is **not** a parallel settings
source: it is loaded into the process environment so YAML values can use
`$VAR` / `${VAR}` substitution (same pattern as ByteDance DeerFlow).

```bash
cp config.yaml.example config.yaml
cp .env.example .env
```

Edit `config.yaml` for non-secret defaults (CORS, DeerFlow URL, OAuth redirect
bases, OSS bucket, etc.). Put secrets and connection strings in `.env`, for
example:

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND_URL`
- `CACHE_REDIS_URL`, `TASK_EVENT_REDIS_URL`, `GENERATION_RATE_LIMIT_REDIS_URL`
- `QWEN_API_KEY` (and optional `DASHSCOPE_API_KEY_SECONDARY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` for the LiteLLM router)
- `DEEP_SEARCHER_BASE_URL` (required for typical chat and source pipelines)
- `OSS_ACCESS_KEY_ID`, `OSS_ACCESS_KEY_SECRET` (and bucket/endpoint in `config.yaml` under `oss`)
- Optional: `MINERU_BASE_URL`, `MINERU_API_KEY` for MinerU PDF parsing
- Optional: `LANGFUSE_*` for traces
- Optional: `GOOGLE_OAUTH_*`, `WEIBO_OAUTH_*`, `QQ_OAUTH_*`, `ALIPAY_*`, WeChat Pay fields
- Optional: `YTDLP_COOKIES_FILE` for Bilibili / yt-dlp

Deep Research uses the **`deer_flow`** section in `config.yaml` (default
`deer_flow_base_url` points at localhost; adjust for your DeerFlow deployment).

> `deploy/middleware/docker-compose-middleware.yml` still contains a `postgres` service,
> but the application runtime is configured for **MySQL** via `database.url` /
> `DATABASE_URL`. The sample `config.yaml.example` comments out the Milvus block;
> retrieval is expected to go through **Deep Searcher**, not local Milvus, unless
> you customize the stack.

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
`deploy/` (for example `deploy/core/docker-compose-core.yml`). For HA and worker
scaling details, see `docs/production-scaling-blueprint.md`.

Useful endpoints after startup:

- App: `http://localhost`
- Frontend dev server: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Health checks: `http://localhost:8000/api/health/live`,
  `http://localhost:8000/api/health/ready`
- Attu (only if you start Milvus + Attu from middleware): `http://localhost:8080`

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

Make sure `DATABASE_URL` in `.env` (and `database.url` in `config.yaml`) points
to a reachable MySQL instance before starting the backend, and that Deep
Searcher is reachable at `deep_searcher_base_url`.

### 2. One-time backend setup

From the repo root (recommended):

```bash
make install
```

This runs `uv sync` in `backend/` and `npm install` in `frontend/`. Equivalent
manual setup:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 3. Run the backend, Celery worker, and frontend (repo root)

From the **repository root**, after `config.yaml`, `.env`, and optionally
`backend-env.sh` are configured:

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
`npm install` or `make install` first).

**Desktop (optional):** with Tauri CLI available, `npm run desktop:dev` from the
repo root starts the desktop shell defined under `src-tauri/`.

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

## Operational Notes

- Source files are stored in object storage; generated slide and infographic
  assets are also served from storage through signed URLs or proxy endpoints.
- Source parsing and studio generation are asynchronous. The frontend should
  either poll resource endpoints or subscribe to task-event SSE streams.
- **Deep Searcher** must be available at `deep_searcher_base_url` for typical
  source processing and chat; tune timeouts and deployment to match your
  environment.
- Optional **MinerU** improves PDF extraction when API keys and
  `mineru` settings are set in `config.yaml` / `.env`.
- Deep Research uses the `deer_flow` block in `config.yaml` and a separate
  DeerFlow deployment. See `backend/docs/DEEP_RESEARCH_DEERFLOW.md` for setup
  details.
- The backend also initializes tables on startup, but running
  `alembic upgrade head` is still recommended for keeping schema changes in
  sync.

## License

MIT
