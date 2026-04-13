# NotebookLM

[English](./README.md)

NotebookLM 是一个基于 Vue 3 和 FastAPI 构建的 AI 研究工作台。它以
Notebook 为组织核心，支持上传或关联多种资料来源，基于检索结果进行
引用式对话，并生成思维导图、演示文稿、信息图、报告以及 Deep Research
研究简报等内容。

## 当前能力

- **以 Notebook 为中心的工作区**，统一管理资料、对话、笔记和生成结果。
- **支持 URL 和文件两种资料接入方式**，当前支持 `pdf`、`docx`、`doc`、
  `txt`、`md`、`csv`、`pptx`、图片、音频和视频。
- **多模态预处理能力**：
  - 图片会通过视觉模型生成内容摘要
  - 音频会通过 Qwen ASR 转写，长音频支持回退方案
  - 视频会通过 Qwen VL 生成内容理解结果
- **带引用的检索式对话**，并支持通过 SSE 返回搜索过程和最终回答。
- **Studio 生成能力**，支持思维导图、演示文稿、信息图、报告和 Deep
  Research 任务。
- **用户笔记与个性化设置**，付费用户可使用更多模型选择能力。
- **JWT 登录 + OAuth 登录**，当前接入 Google、微博、QQ、支付宝。
- **订阅与支付能力**，支持支付宝和微信支付二维码流程。
- **异步任务处理**，基于 Celery，并通过 SSE 提供任务状态流。
- **对象存储集成**，使用阿里云 OSS。
- **链路观测与外部集成**，已支持 Langfuse，并可选接入 DeerFlow。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、TypeScript、Vuetify、Pinia、Vue Router、Vue I18n、Axios |
| 后端 | FastAPI、SQLAlchemy Async、Pydantic Settings、Alembic |
| 业务数据 | 通过 `aiomysql` 连接 MySQL |
| 向量检索 | Milvus |
| 队列与实时通信 | Celery、Redis、SSE |
| AI | LiteLLM、DashScope / Qwen3-Max、Qwen3-VL、Qwen ASR |
| 存储 | 阿里云 OSS |
| 基础设施 | Docker、Nginx |

## 架构概览

1. 前端通过 FastAPI 提供的接口访问 notebooks、sources、chat、notes、
   settings、payment 和 studio 等能力。
2. 上传的原始文件保存在对象存储中，解析后的文本和业务元数据保存在应用
   数据库中。
3. 向量数据存放在 Milvus 中，而不是关系型数据库。
4. 资料处理和 Studio 生成等长耗时任务交给 Celery 执行，并通过任务事件
   SSE 接口回传给前端。
5. Deep Research 是可选的外部集成能力，依赖单独部署的 DeerFlow 网关。

## 仓库结构

```text
notebookLM/
├── frontend/                    # Vue 3 + Vite 前端应用
│   ├── src/api/                 # HTTP 请求封装
│   ├── src/components/          # 资料、对话、Studio、支付等 UI 组件
│   ├── src/stores/              # Pinia 状态管理
│   ├── src/views/               # Landing、Home、Notebook、Login、Pricing、Settings
│   └── src/router/              # 路由定义
├── backend/
│   ├── app/api/                 # FastAPI 路由模块
│   ├── app/ai/                  # LLM、视觉、ASR、检索相关集成
│   ├── app/models/              # SQLAlchemy 模型
│   ├── app/services/            # 业务逻辑
│   ├── app/tasks/               # Celery 任务
│   ├── alembic/                 # 数据库迁移
│   └── docs/                    # 后端功能文档
├── backend.sh                   # 本机启动 FastAPI（可选加载 backend-env.sh）
├── backend-celery.sh            # 本机启动 Celery Worker
├── frontend.sh                  # 本机启动 Vite 开发服务
├── backend-env.sh               # 可选的本机环境覆盖（Redis、数据库、Milvus 等）
├── deploy/
│   ├── middleware/              # 中间件 compose 与 deploy-middleware.sh
│   └── ha/                      # 应用 HA compose 与 deploy-app-ha.sh
├── nginx/                       # 反向代理配置
└── README.md
```

## 环境要求

- Docker 和 Docker Compose
- Node.js 20+
- 建议使用 Python 3.11
- 通过 `DATABASE_URL` 配置一个可访问的 MySQL 实例
- 可用的大模型和对象存储凭证

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

至少需要检查并配置以下变量：

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND_URL`
- `TASK_EVENT_REDIS_URL`
- `MILVUS_URI`
- `QWEN_API_KEY` 或兼容 DashScope 的鉴权配置
- `OSS_*`（含可选的 `OSS_PATH_PREFIX`）
- `CORS_ORIGINS`

可选集成项：

- `DEER_FLOW_BASE_URL`，用于 Deep Research
- `LANGFUSE_*`，用于链路追踪
- `GOOGLE_OAUTH_*`、`WEIBO_OAUTH_*`、`QQ_OAUTH_*`、`ALIPAY_*`
- 微信 / 支付宝回调相关配置

> `deploy/middleware/docker-compose-middleware.yml` 里仍保留了 `postgres` 服务，
> 但当前应用运行时实际围绕 `DATABASE_URL` 配置，默认依赖集也使用
> `aiomysql` 连接 MySQL。向量检索已经迁移到 Milvus。

### 2. 使用 Docker 部署（推荐脚本）

容器部署分为 **中间件** 与 **应用** 两步。

**中间件**（Redis、Milvus、etcd、MinIO、Attu 及相关服务）：

```bash
bash deploy/middleware/deploy-middleware.sh
```

可在任意目录执行，或通过环境变量 `DEPLOY_DIR` 指定仓库根目录。脚本使用
`deploy/middleware/docker-compose-middleware.yml`，会拉取并 `git reset --hard`
到 `origin/master`，再构建并启动栈。需要无缓存构建时可设置 `NO_CACHE=true`。

**应用层**（后端、前端、Nginx、Celery Worker，对应 HA 场景的 compose）：

```bash
bash deploy/ha/deploy-app-ha.sh
```

要求项目根目录存在 `config.yaml`（可先 `cp config.yaml.example config.yaml`）
和 `.env`。脚本使用 `deploy/ha/docker-compose.app-ha.yml` 与
`deploy/ha/docker-compose.workers-ha.yml`，同步到 `origin/master` 后构建
`backend`、`frontend` 镜像并启动。可选：`NO_CACHE=true`；非默认仓库路径时用
`DEPLOY_DIR`。

如需手工组合或沿用旧布局，`deploy/` 下仍有其他 compose 文件（例如
`docker-compose-core.yml`）。高可用与 Worker 扩展细节见
`docs/production-scaling-blueprint.md`。

启动后常用访问地址：

- 应用入口：`http://localhost`
- 前端开发服务：`http://localhost:5173`
- 后端接口文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health/live`、
  `http://localhost:8000/api/health/ready`
- Milvus 可视化工具 Attu：`http://localhost:8080`

## 本地开发

如果你希望前后端直接在本机运行，而把中间件放在 Docker 中，可以按下面
的方式启动：

### 1. 仅启动中间件

```bash
docker compose -f deploy/middleware/docker-compose-middleware.yml up -d redis milvus attu
```

若需与线上一致的完整中间件栈，也可执行部署脚本（注意：会将工作区重置为
`origin/master`）：

```bash
bash deploy/middleware/deploy-middleware.sh
```

启动后端前，请先确保 `DATABASE_URL` 指向一个可访问的 MySQL 实例。

### 2. 后端一次性准备

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 3. 在仓库根目录启动后端、Worker 与前端

配置好 `.env`（以及可选的 `backend-env.sh`）后，在 **仓库根目录** 执行：

```bash
./backend.sh
```

另开终端：

```bash
./backend-celery.sh
```

启动 Vite 开发服务：

```bash
./frontend.sh
```

`backend.sh` 与 `backend-celery.sh` 在存在 `backend/.venv` 时会使用该解释器，
进入 `backend` 目录，并 `source` 仓库根目录下可选的 `backend-env.sh`，用于覆盖
本机 Redis、MySQL、Milvus 等连接（例如指向 `127.0.0.1` 或远程主机）。
`frontend.sh` 在 `frontend/` 下执行 `npm run dev`（需事先在该目录执行过
`npm install`）。

若要通过链接添加 **YouTube** 或 **Bilibili** 视频来源，请在运行 Celery Worker
的环境安装 **`yt-dlp`**（`pip install -r requirements.txt` 已包含该包；程序会
优先使用 `PATH` 中的 `yt-dlp`，否则使用 `python -m yt_dlp`）。

**Bilibili 字幕**多数情况下需要已登录账号的 cookies。请用浏览器扩展导出
`bilibili.com` 的 **Netscape 格式** cookies，在 `.env` 或 `backend-env.sh` 中设置
**`YTDLP_COOKIES_FILE`** 为该文件的绝对路径，并重启 Celery Worker。说明见
[yt-dlp 传递 cookies](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)。

若不使用脚本，也可手动执行等价命令：

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

## 当前产品限制

代码中的角色限制目前为：

| 角色 | Notebook 数量 | 单个 Notebook 资料数 | 每日对话次数 |
| --- | --- | --- | --- |
| `free` | 20 | 30 | 50 |
| `paid` | 200 | 50 | 200 |
| `admin` | 200 | 50 | 9999 |

当前定价页已经接入付费订阅流程，并支持支付宝和微信支付。

## API 概览

以下是当前较核心的接口分组：

| 模块 | 接口 |
| --- | --- |
| 认证 | `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me` |
| OAuth | `/api/auth/oauth/{provider}/start`、`/api/auth/oauth/{provider}/callback` |
| 用户设置 | `GET /api/settings`、`PATCH /api/settings` |
| Notebook | `GET /api/notebooks`、`POST /api/notebooks`、`GET/PUT/DELETE /api/notebooks/{notebook_id}` |
| 资料来源 | `POST /api/notebooks/{notebook_id}/sources`、`POST /api/notebooks/{notebook_id}/sources/upload`、`GET /api/notebooks/{notebook_id}/sources` |
| 对话 | `POST /api/notebooks/{notebook_id}/chat/sessions`、`POST /api/chat/{session_id}/messages`、`POST /api/chat/{session_id}/messages/stream`、`GET /api/chat/{session_id}/messages` |
| 笔记 | Notebook 维度的笔记 CRUD，路径位于 `/api/notebooks/{notebook_id}/notes` |
| Studio | Notebook 维度的思维导图、演示文稿、信息图和报告生成接口 |
| Deep Research | `POST /api/notebooks/{notebook_id}/deep-research`、`GET /api/notebooks/{notebook_id}/deep-research`、`GET /api/deep-research/{report_id}` |
| 任务事件 | `GET /api/task-events/{resource_type}/{resource_id}/stream` |
| 支付 | `POST /api/payment/create`、`GET /api/payment/status/{order_id}` |
| 健康检查 | `GET /api/health`、`GET /api/health/live`、`GET /api/health/ready` |

## 运维说明

- 资料原文件存放在对象存储中；演示文稿和信息图等生成结果也会通过签名 URL
  或代理接口对外提供。
- 资料解析和 Studio 生成是异步流程，前端需要通过轮询资源接口或订阅任务事件
  SSE 来获取状态变化。
- Deep Research 依赖单独部署的 DeerFlow 服务，详细说明见
  `backend/docs/DEEP_RESEARCH_DEERFLOW.md`。
- 后端启动时也会尝试初始化表结构，但为了保持 schema 与迁移一致，仍建议
  显式执行 `alembic upgrade head`。

## License

MIT
