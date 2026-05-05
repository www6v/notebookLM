# NoteWorks - 开源 NotebookLM 替代方案

<p align="center">
  <strong>支持多模型接入 · 多格式文档导入 · 中文深度优化的 AI 知识库工作台</strong>
</p>

<p align="center">
  <a href="https://github.com/www6v/notebookLM/stargazers"><img src="https://img.shields.io/github/stars/www6v/notebookLM?style=social" alt="Stars"></a>
  <a href="https://github.com/www6v/notebookLM/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/www6v/notebookLM/issues"><img src="https://img.shields.io/github/issues/www6v/notebookLM" alt="Issues"></a>
  <a href="https://github.com/www6v/notebookLM/pulls"><img src="https://img.shields.io/github/issues-pr/www6v/notebookLM" alt="Pull Requests"></a>
</p>

<p align="center">
  <a href="http://www.notebooklm.studio">🌐 在线体验</a> ·
  <a href="https://github.com/www6v/notebookLM">📖 项目文档</a> ·
  <a href="https://github.com/www6v/notebookLM/issues">🐛 反馈问题</a> ·
  <a href="#-社区">💬 加入社区</a> ·
  <a href="./README.md">🇬🇧 English</a>
</p>

---

## ✨ NoteWorks 是什么？

NoteWorks 是一个**开源 AI 研究工作台**——Google [NotebookLM](https://notebooklm.google.com) 的开源替代方案。你可以上传文档、用 AI 与文档对话、生成学习材料和报告——同时**支持任意大模型**，数据完全私有。

> *"NotebookLM 很好用，但只能用 Gemini。NoteWorks 让你自由选择模型，同时获得同样的体验。"*

## 🆚 为什么选 NoteWorks 而不是 NotebookLM？

| 功能 | Google NotebookLM | NoteWorks（开源） |
|---|---|---|
| **模型支持** | 仅 Gemini | ✅ OpenAI、Claude、通义千问、Gemini、本地模型 |
| **私有部署** | ❌ 仅云端 | ✅ 完整 Docker 部署 |
| **数据隐私** | Google 服务器 | ✅ 完全自有基础设施 |
| **中文支持** | 一般 | ✅ 深度中文优化 |
| **文档格式** | PDF、TXT | ✅ PDF、DOCX、PPTX、CSV、MD、图片、音频、视频 |
| **深度搜索** | ✅ | ✅ 兼容 Deep Searcher |
| **内容生成** | 有限 | ✅ 思维导图、PPT、信息图、报告 |
| **多用户** | ❌ | ✅ JWT + OAuth（Google、微博、QQ、支付宝） |
| **费用** | 免费 | ✅ 免费开源（MIT） |
| **支付集成** | 无 | ✅ 支付宝、微信支付 |

## 🎯 快速预览

<!-- 替换为实际 GIF：录制 10 秒屏幕演示：上传 PDF → 选择模型 → 提问 → 获得带引用的回答 -->
<!-- 可用 LICEcap、ScreenToGif 或 peek 等工具制作 GIF -->
<p align="center">
  <img src="https://via.placeholder.com/800x450/1a1a2e/16213e?text=演示GIF%3A+上传+%E2%86%92+对话+%E2%86%92+生成" alt="NoteWorks 演示" width="800">
  <br><em>↑ 上传文档 → AI 对话 → 生成成果，全部在一个工作台中完成</em>
</p>

## 🚀 快速开始

### 方式一：在线体验（无需安装）

访问 **[http://www.notebooklm.studio](http://www.notebooklm.studio)** 直接使用。

### 方式二：一键 Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/www6v/notebookLM.git
cd notebookLM

# 配置
cp config.yaml.example config.yaml
cp .env.example .env
# 编辑 .env 填入 API 密钥（QWEN_API_KEY、OPENAI_API_KEY 等）

# 启动
make up-middleware   # 启动 Redis、Milvus、MinIO
make up-ha           # 启动后端 + 前端 + Celery + Nginx
```

访问：`http://localhost`

| 服务 | 地址 |
|---|---|
| 应用 | http://localhost |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/health/live |

### 方式三：本地开发

```bash
git clone https://github.com/www6v/notebookLM.git && cd notebookLM
make install          # 安装依赖（uv + npm）
make up-middleware    # 启动 Redis、Milvus 等中间件
make dev              # 后端
make dev-celery       # Celery 工作进程
make dev-frontend     # Vue 开发服务器
```

完整开发环境配置见 [本地开发](#-本地开发)。

## 🔥 核心功能

### 📚 以笔记本为中心的工作台
围绕笔记本组织研究内容——收集资料、AI 对话、笔记记录、成果生成，一站式完成。

### 📄 多格式文档导入
支持上传或链接任意格式的资料：

| 类型 | 格式 | 处理方式 |
|---|---|---|
| **文档** | PDF、DOCX、DOC、TXT、MD、CSV、PPTX | 文本提取 + 可选 MinerU 高质量 PDF→Markdown |
| **图片** | PNG、JPG、WebP 等 | 视觉模型摘要 |
| **音频** | MP3、WAV、M4A 等 | 通义千问 ASR 转写（支持长音频回退） |
| **视频** | MP4、YouTube、B站链接 | 通义千问 VL 视频摘要 |
| **网页** | 任意 URL | 爬取 + 内容提取 |

### 🤖 多模型支持
基于 **LiteLLM** 路由——接入任意大模型：

- **OpenAI**：GPT-4、GPT-4o、o1、o3
- **Anthropic**：Claude 3.5/4、Sonnet、Opus
- **阿里通义**：Qwen-Max、Qwen-Plus、Qwen-Turbo
- **Google**：Gemini Pro、Gemini Flash
- **本地部署**：任意 OpenAI 兼容接口（Ollama、vLLM 等）

### 🔍 带引用的可信对话
AI 回答基于你的文档，附带**来源引用**——没有幻觉，只有来自知识库的事实。基于 [Deep Searcher](https://github.com/modelscope/Deep-Searcher) 实现。

### 🎨 Studio — 一键生成内容
将研究内容转化为精美输出：
- 🧠 **思维导图** — 可视化知识结构
- 📊 **PPT 演示文稿** — 自动生成幻灯片
- 📰 **信息图** — 数据可视化
- 📝 **研究报告** — 结构化研究总结
- 🔬 **深度研究** — 多步研究简报（基于 [DeerFlow](https://github.com/OpenDeerFlow/DeerFlow)）

### 🔒 私有安全
- 私有部署——数据永不离开你的基础设施
- JWT 认证 + OAuth 登录（Google、微博、QQ、支付宝）
- 阿里云 OSS 对象存储

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      前端（Vue 3）                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│   │ 笔记本   │  │ 文档导入  │  │ AI 对话  │  │ 内容生成  │  │
│   │ 工作台   │  │ 解析     │  │ 带引用   │  │ Studio    │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
└────────┼──────────────┼─────────────┼──────────────┼─────────┘
         │              │             │              │
         ▼              ▼             ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   后端（FastAPI）                             │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────────┐ │
│  │ 笔记本管理  │  │ 文档解析  │  │ AI（LiteLLM 路由）      │ │
│  │            │  │           │  │ 千问 / OpenAI / 等      │ │
│  └─────┬──────┘  └─────┬─────┘  └───────────┬────────────┘ │
│        │               │                     │              │
│        ▼               ▼                     ▼              │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────┐     │
│  │  MySQL    │  │ Deep Searcher│  │ Celery + Redis    │     │
│  │  (元数据)  │  │ (RAG/检索)   │  │ (异步任务)        │     │
│  └───────────┘  └──────────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  阿里云 OSS     │   │   Milvus /      │
│  (文件存储)     │   │   向量数据库     │
└─────────────────┘   └─────────────────┘
```

## 🛠️ 技术栈

| 层级 | 技术 |
|---|---|
| **前端** | Vue 3、Vite、TypeScript、Vuetify、Pinia、Vue Router、Vue I18n、Axios |
| **后端** | FastAPI、SQLAlchemy（异步）、Pydantic Settings、Alembic |
| **数据库** | MySQL（aiomysql） |
| **检索** | Deep Searcher（HTTP）；通义 DashScope 嵌入；Milvus（可选） |
| **队列** | Celery + Redis + SSE 流式 |
| **AI** | LiteLLM 路由、通义千问、OpenAI、Gemini |
| **存储** | 阿里云 OSS |
| **基础设施** | Docker、Docker Compose、Nginx |

## 📁 项目结构

```
notebookLM/
├── config.yaml.example          # 配置模板（复制为 config.yaml）
├── .env.example                 # 密钥模板（复制为 .env）
├── frontend/                    # Vue 3 + Vite 应用
├── src-tauri/                   # 可选 Tauri 桌面客户端
├── backend/
│   ├── app/api/                 # FastAPI 路由
│   ├── app/ai/                  # LLM、视觉、ASR 集成
│   ├── app/models/              # SQLAlchemy 模型
│   ├── app/services/            # 业务逻辑
│   ├── app/tasks/               # Celery 任务
│   ├── alembic/                 # 数据库迁移
│   └── docs/                    # 后端功能文档
├── deploy/                      # Docker Compose 文件
│   ├── core/                    # 核心服务
│   ├── middleware/              # Redis、Milvus、MinIO
│   └── ha/                      # 高可用应用编排
├── nginx/                       # 反向代理配置
├── makefile                     # make install / dev / up-middleware / up-ha
└── README.md
```

## ⚙️ 配置说明

### 必填配置

编辑 `.env` 填入你的密钥：

```bash
# 必需
SECRET_KEY=your-secret-key
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/dbname
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# AI 模型（至少一个）
QWEN_API_KEY=your-qwen-key
# OPENAI_API_KEY=your-openai-key
# GEMINI_API_KEY=your-gemini-key

# 对话和文档索引必需
DEEP_SEARCHER_BASE_URL=http://localhost:8001

# 对象存储
OSS_ACCESS_KEY_ID=your-oss-key
OSS_ACCESS_KEY_SECRET=your-oss-secret
```

### 可选集成

| 集成 | 用途 | 配置项 |
|---|---|---|
| **MinerU** | 高质量 PDF→Markdown 解析 | `MINERU_BASE_URL`、`MINERU_API_KEY` |
| **Langfuse** | LLM 链路追踪与观测 | `LANGFUSE_*` |
| **DeerFlow** | 深度研究智能体 | `config.yaml` 中的 `deer_flow_base_url` |
| **OAuth** | Google、微博、QQ、支付宝登录 | `GOOGLE_OAUTH_*`、`WEIBO_OAUTH_*` 等 |
| **支付** | 支付宝、微信支付 | `ALIPAY_*`、微信支付配置 |
| **yt-dlp** | 视频/音频 URL 解析 | `YTDLP_COOKIES_FILE`（B站需要 cookie） |

## 📊 产品限制

| 角色 | 笔记本数 | 每笔记本资料数 | 每日对话数 |
|---|---|---|---|
| `free` | 20 | 30 | 50 |
| `paid` | 200 | 50 | 200 |
| `admin` | 200 | 50 | ∞ |

## 🧑‍💻 本地开发

### 1. 启动中间件

```bash
docker compose -f deploy/middleware/docker-compose-middleware.yml up -d redis milvus
```

### 2. 安装依赖

```bash
make install
# 执行 backend/ 的 `uv sync` 和 frontend/ 的 `npm install`
```

### 3. 运行服务

```bash
# 终端 1：后端
make dev

# 终端 2：Celery 工作进程
make dev-celery

# 终端 3：前端
make dev-frontend
```

或手动运行：

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

### 4. 桌面客户端（可选）

```bash
npm run desktop:dev
```

## 💬 社区

加入我们，获取帮助、分享想法、参与贡献：

- 💬 **Discord**：[加入服务器](https://discord.gg/YOUR_INVITE_LINK) *（替换为你的邀请链接）*
- 📱 **微信群**：扫码加入 *（添加二维码图片）*
- 🐛 **GitHub Issues**：[反馈问题或请求功能](https://github.com/www6v/notebookLM/issues)
- 💡 **Discussions**：[分享你的使用场景](https://github.com/www6v/notebookLM/discussions)

## 🤝 贡献指南

欢迎贡献！开始方式：

1. Fork 本项目
2. 创建特性分支（`git checkout -b feature/amazing-feature`）
3. 提交修改（`git commit -m 'Add amazing feature'`）
4. 推送分支（`git push origin feature/amazing-feature`）
5. 发起 Pull Request

查看 [`good first issue`](https://github.com/www6v/notebookLM/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) 标签，找到适合新手的任务。

## 📜 开源协议

本项目基于 [MIT License](./LICENSE) 开源。

---

<p align="center">
  由 <a href="https://github.com/www6v">@www6v</a> 用 ❤️ 打造 ·
  <a href="https://github.com/www6v/notebookLM">Star 本项目</a> 支持开发 ⭐
</p>
