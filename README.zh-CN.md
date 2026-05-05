# NoteWorks - 开源 NotebookLM

[English](./README.md)

NoteWorks 是一个基于 Vue 3 和 FastAPI 构建的 AI 研究工作台。它以
Notebook 为组织核心，支持上传或关联多种资料来源，基于检索结果进行
引用式对话，并生成思维导图、演示文稿、信息图、报告以及 Deep Research
研究简报等内容。

## 当前能力

- **以 Notebook 为中心的工作区**，统一管理资料、对话、笔记和生成结果。
- **支持 URL 和文件两种资料接入方式**，当前支持 `pdf`、`docx`、`doc`、
  `txt`、`md`、`csv`、`pptx`、图片、音频和视频。
- **可选 MinerU 集成**：配置 `MINERU_API_KEY` 等后，可对 PDF 做更高质量的
  Markdown 解析。
- **多模态预处理能力**：
  - 图片会通过视觉模型生成内容摘要
  - 音频会通过 Qwen ASR 转写，长音频支持回退方案
  - 视频会通过 Qwen VL 生成内容理解结果
- **带引用的检索式对话**，由 **Deep Searcher** HTTP 服务（上传 /
  load-files / query）支撑；资料与 Studio 等长任务通过 **SSE 任务事件**
  推送进度。
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
| 检索与索引 | Deep Searcher（远程 HTTP）；向量嵌入走 DashScope；中间件 Compose 中可带 Milvus（兼容/配套，示例配置中已注释） |
| 队列与实时通信 | Celery、Redis、SSE |
| AI | LiteLLM 路由、DashScope（Qwen 对话 / VL / ASR / 嵌入），可选 OpenAI / Gemini 密钥 |
| 存储 | 阿里云 OSS |
| 基础设施 | Docker、Nginx |

## 架构概览

1. 前端通过 FastAPI 提供的接口访问 notebooks、sources、chat、notes、
   settings、payment 和 studio 等能力。
2. 上传的原始文件保存在对象存储中，解析后的文本和业务元数据保存在应用
   数据库中。
3. **资料入库与对话问答**走配置的 **Deep Searcher** 基地址（见
   `config.yaml` 中 `deep_searcher`）。示例 `config.yaml.example` 中 Milvus
   段为注释状态；中间件里仍可启动 Milvus 以配合其他或历史部署。
4. 资料处理和 Studio 生成等长耗时任务交给 Celery 执行，并通过任务事件
   SSE 接口回传给前端。
5. Deep Research 是可选的外部集成能力，依赖单独部署的 DeerFlow 网关（
   `config.yaml` 中 `deer_flow`）。

## 仓库结构

```text
notebookLM/
├── config.yaml.example          # 应用配置模板（复制为 config.yaml）
├── .env.example                 # 供 config.yaml 中 $VAR 展开用的密钥与连接串
├── frontend/                    # Vue 3 + Vite 前端应用
│   ├── src/api/                 # HTTP 请求封装
│   ├── src/components/          # 资料、对话、Studio、支付等 UI 组件
│   ├── src/stores/              # Pinia 状态管理
│   ├── src/views/               # Landing、Home、Notebook、Login、Pricing、Settings
│   └── src/router/              # 路由定义
├── src-tauri/                   # 可选 Tauri 桌面端（见根目录 package.json 脚本）
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
├── backend-env.sh               # 可选的本机环境覆盖（Redis、数据库等）
├── makefile                     # make install / dev / up-middleware / up-ha
├── deploy/
│   ├── core/                    # 核心 compose 辅助脚本
│   ├── middleware/              # 中间件 compose 与 deploy-middleware.sh
│   └── ha/                      # 应用 HA compose 与 deploy-app-ha.sh
├── nginx/                       # 反向代理配置
└── README.md
```

## 环境要求

- Docker 和 Docker Compose
- Node.js 20+
- 建议使用 Python 3.11（可选安装 [uv](https://github.com/astral-sh/uv)，
  `make install` 会在后端目录执行 `uv sync`）
- 可访问的 MySQL（由 `config.yaml` 的 `database.url` 指定，通常对应 `.env` 中
  `DATABASE_URL`）
- 可访问的 **Deep Searcher** 服务（`deep_searcher.deep_searcher_base_url`），
  用于典型资料索引与对话流程
- 大模型与对象存储相关凭证

## 快速开始

### 1. 配置 `config.yaml` 与 `.env`

后端从仓库根目录读取 **`config.yaml`**（可用环境变量
`NOTEBOOKLM_CONFIG_PATH` 覆盖路径）。**`.env` 不是**与 YAML 并列的第二套配置
源：仅将变量加载到进程环境，供 YAML 字符串中的 `$VAR` / `${VAR}` 替换（与
ByteDance DeerFlow 的用法一致）。

```bash
cp config.yaml.example config.yaml
cp .env.example .env
```

非敏感默认值（CORS、DeerFlow 地址、OAuth 回调基址、OSS bucket 等）放在
`config.yaml`。密钥与连接串放在 `.env`，例如：

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`、`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND_URL`
- `CACHE_REDIS_URL`、`TASK_EVENT_REDIS_URL`、`GENERATION_RATE_LIMIT_REDIS_URL`
- `QWEN_API_KEY`（以及可选的 `DASHSCOPE_API_KEY_SECONDARY`、`OPENAI_API_KEY`、
  `GEMINI_API_KEY`，供 LiteLLM 路由使用）
- `DEEP_SEARCHER_BASE_URL`（常规对话与资料流水线需要）
- `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`（endpoint、bucket 等在
  `config.yaml` 的 `oss` 段）
- 可选：`MINERU_BASE_URL`、`MINERU_API_KEY`（MinerU PDF 解析）
- 可选：`LANGFUSE_*`（链路追踪）
- 可选：`GOOGLE_OAUTH_*`、`WEIBO_OAUTH_*`、`QQ_OAUTH_*`、`ALIPAY_*`、微信支付
  相关字段
- 可选：`YTDLP_COOKIES_FILE`（Bilibili / yt-dlp）

Deep Research 使用 `config.yaml` 中的 **`deer_flow`**（默认
`deer_flow_base_url` 指向本机，请按实际 DeerFlow 部署修改）。

> `deploy/middleware/docker-compose-middleware.yml` 里仍保留了 `postgres` 服务，
> 但应用运行时使用 **MySQL**（`database.url` / `DATABASE_URL`）。示例
> `config.yaml.example` 中 Milvus 配置为注释；检索预期走 **Deep Searcher**，
> 除非自行扩展中间件与配置。

### 2. 使用 Docker 部署（推荐 Make 或脚本）

容器部署分为 **中间件** 与 **应用** 两步。

**中间件**（Redis、Milvus、etcd、MinIO、Attu 及相关服务）：

```bash
make up-middleware
```

等价于执行 `deploy/middleware/deploy-middleware.sh`（会同步到 `origin/master`
并构建启动）。需要无缓存构建时可设置 `NO_CACHE=true`。

**应用层**（后端、前端、Nginx、Celery Worker，HA compose）：

```bash
make up-ha
```

或直接使用脚本（可在任意目录执行，或通过 `DEPLOY_DIR` 指定仓库根目录；中间件
脚本会 `git reset --hard` 到 `origin/master`；`NO_CACHE=true` 可无缓存构建）：

```bash
bash deploy/middleware/deploy-middleware.sh
```

```bash
bash deploy/ha/deploy-app-ha.sh
```

要求项目根目录存在 `config.yaml` 与 `.env`。脚本使用
`deploy/ha/docker-compose.app-ha.yml` 与
`deploy/ha/docker-compose.workers-ha.yml`。可选：`NO_CACHE=true`；非默认仓库
路径时用 `DEPLOY_DIR`。

如需手工组合或沿用旧布局，`deploy/core/` 等目录下另有 compose 与脚本。高可用
与 Worker 扩展见 `docs/production-scaling-blueprint.md`。

启动后常用访问地址：

- 应用入口：`http://localhost`
- 前端开发服务：`http://localhost:5173`
- 后端接口文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health/live`、
  `http://localhost:8000/api/health/ready`
- Attu（仅当从中间件启动 Milvus + Attu 时）：`http://localhost:8080`

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

启动后端前，请确保 `.env` 中的 `DATABASE_URL` 与 `config.yaml` 中数据库配置
指向可访问的 MySQL，且 **Deep Searcher** 在 `deep_searcher_base_url` 可达。

### 2. 后端与前端依赖（一次性）

在仓库根目录推荐：

```bash
make install
```

会在 `backend/` 执行 `uv sync`，在 `frontend/` 执行 `npm install`。也可手动：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 3. 在仓库根目录启动后端、Worker 与前端

配置好 `config.yaml`、`.env`（以及可选的 `backend-env.sh`）后，在 **仓库根目录**
可使用 Make：

```bash
make dev
```

另开终端：

```bash
make dev-celery
```

启动 Vite：

```bash
make dev-frontend
```

或直接执行脚本：`./backend.sh`、`./backend-celery.sh`、`./frontend.sh`。

`backend.sh` 与 `backend-celery.sh` 在存在 `backend/.venv` 时会使用该解释器，
进入 `backend` 目录，并 `source` 仓库根目录下可选的 `backend-env.sh`，用于覆盖
本机 Redis、MySQL 等连接（例如指向 `127.0.0.1` 或远程主机）。
`frontend.sh` 在 `frontend/` 下执行 `npm run dev`（需事先 `make install` 或
`npm install`）。

**桌面端（可选）：** 在仓库根目录执行 `npm run desktop:dev` 可启动 `src-tauri/`
定义的 Tauri 外壳。

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

## 运维说明

- 资料原文件存放在对象存储中；演示文稿和信息图等生成结果也会通过签名 URL
  或代理接口对外提供。
- 资料解析和 Studio 生成是异步流程，前端需要通过轮询资源接口或订阅任务事件
  SSE 来获取状态变化。
- **`deep_searcher_base_url` 必须可用**，典型资料处理与对话依赖该服务；请按环境
  调整超时与部署拓扑。
- 配置 **MinerU**（`config.yaml` 的 `mineru` 段与 `.env` 中的 `MINERU_*`）可提升
  PDF 抽取质量。
- Deep Research 使用 `config.yaml` 中的 `deer_flow`，并依赖单独部署的 DeerFlow；
  详见 `backend/docs/DEEP_RESEARCH_DEERFLOW.md`。
- 后端启动时也会尝试初始化表结构，但为了保持 schema 与迁移一致，仍建议
  显式执行 `alembic upgrade head`。

## License

MIT
