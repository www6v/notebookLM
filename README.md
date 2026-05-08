# NoteWorks - Open NotebookLM Alternative

<p align="center">
  <strong>AI Knowledge Workspace with Multi-Model Support, Deep Search & Chinese-First Experience</strong>
</p>

<p align="center">
  <a href="https://github.com/www6v/notebookLM/stargazers"><img src="https://img.shields.io/github/stars/www6v/notebookLM?style=social" alt="Stars"></a>
  <a href="https://github.com/www6v/notebookLM/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/www6v/notebookLM/issues"><img src="https://img.shields.io/github/issues/www6v/notebookLM" alt="Issues"></a>
  <a href="https://github.com/www6v/notebookLM/pulls"><img src="https://img.shields.io/github/issues-pr/www6v/notebookLM" alt="Pull Requests"></a>
  <a href="https://github.com/www6v/notebookLM"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python"></a>
  <a href="https://github.com/www6v/notebookLM"><img src="https://img.shields.io/badge/Vue-3-42b883.svg" alt="Vue"></a>
</p>

<p align="center">
  <a href="http://www.notebooklm.studio">🌐 Live Demo</a> ·
  <a href="https://github.com/www6v/notebookLM">📖 Documentation</a> ·
  <a href="https://github.com/www6v/notebookLM/issues">🐛 Report Bug</a> ·
  <a href="#-community">💬 Community</a> ·
  <a href="./README.zh-CN.md">🇨🇳 中文文档</a>
</p>

---

## ✨ What is NoteWorks?

NoteWorks is an **open-source AI research workspace** — a self-hosted alternative to [Google's NotebookLM](https://notebooklm.google.com). It lets you upload documents, chat with them using AI, and generate study materials, reports, and presentations — all while **supporting any LLM** and keeping your data private.

> *"NotebookLM is powerful but locked to Gemini. NoteWorks gives you the same experience with your choice of models."*

## 🆚 Why NoteWorks over NotebookLM?

| Feature | Google NotebookLM | NoteWorks (Open Source) |
|---|---|---|
| **Models** | Gemini only | ✅ OpenAI, Claude, Qwen, Gemini, local models |
| **Self-hosting** | ❌ Cloud only | ✅ Full Docker deployment |
| **Data privacy** | Google servers | ✅ Your own infrastructure |
| **Chinese support** | Limited | ✅ Deeply optimized for Chinese |
| **Document formats** | PDF, TXT | ✅ PDF, DOCX, PPTX, CSV, MD, images, audio, video |
| **Deep Search** | ✅ | ✅ Compatible with Deep Searcher |
| **Studio outputs** | Limited | ✅ Mind maps, slides, infographics, reports |
| **Multi-user** | ❌ | ✅ JWT auth + OAuth (Google, Weibo, QQ, Alipay) |
| **Cost** | Free | ✅ Free & open source (MIT) |
| **Payments** | N/A | ✅ Alipay & WeChat Pay integration |

## 🎯 Quick Preview

<!-- Replace with actual GIF: Record a 10-second screen capture showing: Upload PDF → Select Model → Ask Question → Get Answer with Citations -->
<!-- You can use tools like LICEcap, ScreenToGif, or peek to create the GIF -->
<p align="center">
  <img src="https://via.placeholder.com/800x450/1a1a2e/16213e?text=Demo+GIF%3A+Upload+%E2%86%92+Chat+%E2%86%92+Generate" alt="NoteWorks Demo" width="800">
  <br><em>↑ Upload documents, chat with AI, generate artifacts — all in one workspace</em>
</p>

## 🚀 Quick Start

### Option 1: Try Online (No Setup)

Visit **[http://www.notebooklm.studio](http://www.notebooklm.studio)** for a live demo.

### Option 2: One-Click Docker Deploy (Recommended)

```bash
# Clone the repo
git clone https://github.com/www6v/notebookLM.git
cd notebookLM

# Configure
cp config.yaml.example config.yaml
cp .env.example .env
# Edit .env with your API keys (QWEN_API_KEY, OPENAI_API_KEY, etc.)

# Start everything
make up-middleware   # Redis, Milvus, MinIO
make up-ha           # Backend + Frontend + Celery + Nginx
```

Access at: `http://localhost`

| Service | URL |
|---|---|
| App | http://localhost |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/health/live |

### Option 3: Local Development

```bash
git clone https://github.com/www6v/notebookLM.git && cd notebookLM
make install          # Install dependencies (uv + npm)
make up-middleware    # Start Redis, Milvus, etc.
make dev              # Backend
make dev-celery       # Celery worker
make dev-frontend     # Vue dev server
```

See [Local Development](#-local-development) for full setup instructions.

## 🔥 Key Features

### 📚 Notebook-Centric Workspace
Organize research around notebooks — collect sources, chat with AI, take notes, and generate artifacts in one place.

### 📄 Multi-Format Document Ingestion
Upload or link sources in any format:

| Type | Formats | Processing |
|---|---|---|
| **Documents** | PDF, DOCX, DOC, TXT, MD, CSV, PPTX | Text extraction + optional MinerU for high-quality PDF→Markdown |
| **Images** | PNG, JPG, WebP, etc. | Vision model summarization |
| **Audio** | MP3, WAV, M4A, etc. | Qwen ASR transcription (with long-audio fallback) |
| **Video** | MP4, YouTube, Bilibili URLs | Qwen VL video summarization |
| **URLs** | Any web page | Crawling + content extraction |

### 🤖 Multi-Model Support
Powered by **LiteLLM** router — connect any LLM:

- **OpenAI**: GPT-4, GPT-4o, o1, o3
- **Anthropic**: Claude 3.5/4, Sonnet, Opus
- **Alibaba**: Qwen-Max, Qwen-Plus, Qwen-Turbo
- **Google**: Gemini Pro, Gemini Flash
- **Local**: Any OpenAI-compatible endpoint (Ollama, vLLM, etc.)

### 🔍 Grounded Chat with Citations
AI answers are grounded in your documents with **source citations** — no hallucination, just facts from your knowledge base. Powered by [Deep Searcher](https://github.com/modelscope/Deep-Searcher).

### 🎨 Studio — Generate Artifacts
Transform your research into polished outputs:
- 🧠 **Mind Maps** — Visual knowledge structures
- 📊 **Slide Decks** — Auto-generated presentations
- 📰 **Infographics** — Data visualization
- 📝 **Reports** — Structured research summaries
- 🔬 **Deep Research** — Multi-step research briefs (via [DeerFlow](https://github.com/OpenDeerFlow/DeerFlow))

### 🔒 Private & Secure
- Self-hosted — your data never leaves your infrastructure
- JWT authentication + OAuth login (Google, Weibo, QQ, Alipay)
- Object storage with Alibaba Cloud OSS

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                       │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│   │ Notebook │  │  Source  │  │   Chat   │  │   Studio  │  │
│   │  Workspace│  │ Ingestion│  │  w/ Cit. │  │ Generator │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
└────────┼──────────────┼─────────────┼──────────────┼─────────┘
         │              │             │              │
         ▼              ▼             ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────────┐ │
│  │  Notebook  │  │  Source   │  │   AI (LiteLLM Router)  │ │
│  │  Manager   │  │  Parser   │  │   Qwen / OpenAI / etc  │ │
│  └─────┬──────┘  └─────┬─────┘  └───────────┬────────────┘ │
│        │               │                     │              │
│        ▼               ▼                     ▼              │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │  MySQL    │  │  Deep Searcher│  │  Celery + Redis   │     │
│  │  (meta)   │  │  (RAG/Retrieval)│  │  (async tasks)   │     │
│  └───────────┘  └──────────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  Alibaba OSS    │   │   Milvus /      │
│  (file storage) │   │   Vector DB     │
└─────────────────┘   └─────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Vue 3, Vite, TypeScript, Vuetify, Pinia, Vue Router, Vue I18n, Axios |
| **Backend** | FastAPI, SQLAlchemy (async), Pydantic Settings, Alembic |
| **Database** | MySQL via `aiomysql` |
| **Retrieval** | Deep Searcher (HTTP); DashScope embeddings; Milvus (optional) |
| **Queue** | Celery + Redis + SSE streaming |
| **AI** | LiteLLM router, DashScope (Qwen), OpenAI, Gemini |
| **Storage** | Alibaba Cloud OSS |
| **Infra** | Docker, Docker Compose, Nginx |

## 📁 Repository Structure

```
notebookLM/
├── config.yaml.example          # Config template (copy to config.yaml)
├── .env.example                 # Secrets template (copy to .env)
├── frontend/                    # Vue 3 + Vite application
├── src-tauri/                   # Optional Tauri desktop shell
├── backend/
│   ├── app/api/                 # FastAPI routes
│   ├── app/ai/                  # LLM, vision, ASR integrations
│   ├── app/models/              # SQLAlchemy models
│   ├── app/services/            # Business logic
│   ├── app/tasks/               # Celery tasks
│   ├── alembic/                 # DB migrations
│   └── docs/                    # Backend feature docs
├── deploy/                      # Docker Compose files
│   ├── core/                    # Core services
│   ├── middleware/              # Redis, Milvus, MinIO
│   └── ha/                      # High-availability app compose
├── nginx/                       # Reverse proxy configs
├── makefile                     # make install / dev / up-middleware / up-ha
└── README.md
```

## ⚙️ Configuration

### Required Settings

Edit `.env` with your credentials:

```bash
# Essential
SECRET_KEY=your-secret-key
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/dbname
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# AI Models (at least one)
QWEN_API_KEY=your-qwen-key
# OPENAI_API_KEY=your-openai-key
# GEMINI_API_KEY=your-gemini-key

# Required for chat & source indexing
DEEP_SEARCHER_BASE_URL=http://localhost:8001

# Object Storage
OSS_ACCESS_KEY_ID=your-oss-key
OSS_ACCESS_KEY_SECRET=your-oss-secret
```

### Optional Integrations

| Integration | Purpose | Config |
|---|---|---|
| **MinerU** | High-quality PDF→Markdown parsing | `MINERU_BASE_URL`, `MINERU_API_KEY` |
| **Langfuse** | LLM tracing & observability | `LANGFUSE_*` |
| **DeerFlow** | Deep Research agent | `deer_flow_base_url` in `config.yaml` |
| **OAuth** | Google, Weibo, QQ, Alipay login | `GOOGLE_OAUTH_*`, `WEIBO_OAUTH_*`, etc. |
| **Payments** | Alipay & WeChat Pay | `ALIPAY_*`, WeChat Pay fields |
| **yt-dlp** | Video/audio from URLs | `YTDLP_COOKIES_FILE` for Bilibili |

## 📊 Product Limits

| Role | Notebooks | Sources/notebook | Daily Chats |
|---|---|---|---|
| `free` | 20 | 30 | 50 |
| `paid` | 200 | 50 | 200 |
| `admin` | 200 | 50 | ∞ |

## 🧑‍💻 Local Development

### 1. Start Middleware

```bash
docker compose -f deploy/middleware/docker-compose-middleware.yml up -d redis milvus
```

### 2. Install Dependencies

```bash
make install
# This runs `uv sync` in backend/ and `npm install` in frontend/
```

### 3. Run Services

```bash
# Terminal 1: Backend
make dev

# Terminal 2: Celery Worker
make dev-celery

# Terminal 3: Frontend
make dev-frontend
```

Or run manually:

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

### 4. Desktop App (Optional)

```bash
npm run desktop:dev
```

## 💬 Community

Join us to get help, share ideas, and contribute:

- 💬 **Discord**: [Join Server](https://discord.gg/YOUR_INVITE_LINK) *(replace with your link)*
- 📱 **WeChat Group**: Scan QR code *(add QR image here)*
- 🐛 **GitHub Issues**: [Report bugs or request features](https://github.com/www6v/notebookLM/issues)
- 💡 **Discussions**: [Share your use cases](https://github.com/www6v/notebookLM/discussions)

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Check out [issues labeled `good first issue`](https://github.com/www6v/notebookLM/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) for beginner-friendly tasks.

## 📜 License

This project is licensed under the [MIT License](./LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/www6v">@www6v</a> ·
  <a href="https://github.com/www6v/notebookLM">Star this repo</a> to support development ⭐
</p>




