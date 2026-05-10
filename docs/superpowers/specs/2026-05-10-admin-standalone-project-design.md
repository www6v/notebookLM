# Admin 独立部署项目设计

**日期：** 2026-05-10  
**状态：** 已批准  
**目标目录：** `admin/`

---

## 背景

主项目 notebookLM 中存在后台管理功能，分散在：

- 前端：`frontend/src/views/admin/`（4 个 Vue 页面）+ admin 路由
- 后端：`backend/app/api/admin.py`（FastAPI `/api/admin` 路由）

目标是将这两部分提取到 `admin/` 目录，形成可独立部署的完整项目（前端 + 后端），通过 Docker Compose 一键启动。

---

## 技术选型

| 层 | 技术栈 |
|----|--------|
| Admin 前端 | Vue 3 + Vite + TypeScript + Vuetify 3（与主前端相同） |
| Admin 后端 | FastAPI + uvicorn（与主后端相同） |
| 共享模块 | Python 包 `notebooklm-shared`（位于 `shared/`） |
| 数据库 | 共享主项目的 MySQL + Redis（同一实例） |
| 部署 | Docker Compose（挂载到主项目 Docker 网络） |

---

## 目录结构

```
notebookLM/
├── shared/                              # 新增：共享 Python 包
│   ├── pyproject.toml                   # name = "notebooklm-shared"
│   └── notebooklm_shared/
│       ├── __init__.py
│       ├── config.py                    # 从 backend/app/config.py 迁移
│       ├── database.py                  # 从 backend/app/database.py 迁移
│       ├── models/                      # 从 backend/app/models/ 迁移
│       └── auth/
│           ├── jwt.py                   # JWT 核心逻辑（create/verify token）
│           └── deps.py                  # FastAPI 依赖注入（get_current_user, require_admin）
│
├── backend/                             # 小改动：imports 指向 notebooklm_shared
│   └── pyproject.toml                   # 新增 "notebooklm-shared @ ../shared"
│
├── admin/
│   ├── frontend/                        # 独立 Vue 3 应用
│   │   ├── package.json
│   │   ├── vite.config.ts               # dev proxy /api → admin-backend:8000
│   │   ├── src/
│   │   │   ├── views/
│   │   │   │   ├── LoginPage.vue        # 独立登录页
│   │   │   │   └── admin/               # 4 个 admin 页面（从主前端迁移）
│   │   │   │       ├── AdminUserList.vue
│   │   │   │       ├── AdminUserDetail.vue
│   │   │   │       ├── AdminFeaturedNotebooksPage.vue
│   │   │   │       └── AdminDesktopPage.vue
│   │   │   ├── api/
│   │   │   │   ├── client.ts            # axios 实例，baseURL = '/api'
│   │   │   │   ├── auth.ts              # login API
│   │   │   │   └── admin.ts             # admin CRUD API
│   │   │   ├── stores/
│   │   │   │   └── useUserStore.ts      # 登录态管理
│   │   │   └── router/
│   │   │       └── index.ts             # 只含 /login 和 /admin/* 路由
│   │   ├── nginx.conf                   # SPA fallback + /api proxy 到 admin-backend
│   │   └── Dockerfile                   # 多阶段：Node builder → nginx:alpine
│   │
│   ├── backend/                         # 独立 FastAPI 应用
│   │   ├── pyproject.toml               # 依赖 notebooklm-shared @ ../../shared
│   │   ├── app/
│   │   │   ├── main.py                  # 只注册 admin + auth router
│   │   │   ├── api/
│   │   │   │   ├── admin.py             # 从 backend 迁移的 admin 路由
│   │   │   │   └── auth.py              # /api/auth/login 端点
│   │   │   └── deps.py                  # 引用 notebooklm_shared.auth.deps
│   │   ├── config.yaml.example          # 只含 database/redis/jwt 配置
│   │   ├── .env.example                 # 数据库密码、JWT secret 等
│   │   └── Dockerfile
│   │
│   ├── docker-compose.yml               # 一键启动 admin-frontend + admin-backend
│   └── README.md                        # 部署说明
│
├── frontend/                            # 不变
└── ...
```

---

## 数据流

```
用户浏览器
    │
    ▼
admin-frontend nginx :80
    ├── /api/*  ──proxy──▶  admin-backend :8000 (FastAPI)
    │                             │
    │                             ▼
    │                       notebooklm_shared
    │                       (models / auth / config / database)
    │                             │
    │                             ▼
    │                       MySQL (共享) / Redis (共享)
    │
    └── /*      ──static──▶ Vue SPA /dist
```

---

## shared/ 包设计

### 包元数据（pyproject.toml）

```toml
[project]
name = "notebooklm-shared"
version = "0.1.0"
dependencies = [
    "sqlalchemy[asyncio]",
    "aiomysql",
    "pydantic-settings",
    "python-jose[cryptography]",
    "bcrypt",
    "pyyaml",
]
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `config.py` | `Settings` 类，读取 config.yaml + .env，支持 `$VAR` 扩展 |
| `database.py` | SQLAlchemy async engine、`SessionLocal`、`Base`、`get_db` |
| `models/` | 所有 ORM 模型（User、Notebook、Source 等） |
| `auth/jwt.py` | `create_access_token`、`verify_token`、`get_password_hash`、`verify_password` |
| `auth/deps.py` | FastAPI 依赖：`get_current_user`、`require_admin` |

**约束：** `shared/` 只引用第三方库，不引用 `backend/` 或 `admin/` 任何模块，避免循环依赖。

---

## admin/backend/ 设计

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户名+密码登录，返回 JWT |
| GET | `/api/admin/users` | 用户列表（分页） |
| GET | `/api/admin/users/{id}` | 用户详情 + 笔记本统计 |
| PATCH | `/api/admin/users/{id}` | 修改用户角色/状态 |
| GET | `/api/admin/featured-notebooks` | 获取精选笔记本 |
| PUT | `/api/admin/featured-notebooks` | 更新精选笔记本 |
| PUT | `/api/admin/client-config` | 设置桌面端后端 URL |

所有 `/api/admin/*` 路由通过 `require_admin` 依赖守卫（来自 `notebooklm_shared.auth.deps`）。

### config.yaml.example（精简）

```yaml
database:
  host: "localhost"
  port: 3306
  name: "notebooklm"
  user: "root"
  password: "${DB_PASSWORD}"

redis:
  host: "localhost"
  port: 6379

application:
  secret_key: "${SECRET_KEY}"
  access_token_expire_minutes: 1440
```

---

## admin/frontend/ 设计

### 路由结构

```
/login              → LoginPage.vue     （无需鉴权）
/admin              → AdminUserList     （requiresAuth + requiresAdmin）
/admin/users/:id    → AdminUserDetail   （requiresAuth + requiresAdmin）
/admin/featured     → AdminFeaturedNotebooksPage
/admin/desktop      → AdminDesktopPage
```

路由守卫：检查 localStorage token，无效则跳转 `/login`。

### nginx.conf（容器内）

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    location /api/ {
        proxy_pass http://admin-backend:8000;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## docker-compose.yml 设计

```yaml
services:
  admin-backend:
    build: ./backend
    env_file: ./backend/.env
    volumes:
      - ./backend/config.yaml:/app/config.yaml:ro
    networks:
      - notebooklm_default

  admin-frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - admin-backend
    networks:
      - notebooklm_default

networks:
  notebooklm_default:
    external: true
```

**前提：** 主项目的 middleware（MySQL、Redis）已通过 `make up-middleware` 启动，`notebooklm_default` 网络已存在。

---

## 主 backend 改动

### import 替换规则

| 原路径 | 新路径 |
|--------|--------|
| `from app.config import settings` | `from notebooklm_shared.config import settings` |
| `from app.database import ...` | `from notebooklm_shared.database import ...` |
| `from app.models import ...` | `from notebooklm_shared.models import ...` |
| `from app.api.deps import ...` | `from notebooklm_shared.auth.deps import ...` |

影响约 50 个文件，全部为机械性 import 替换，业务逻辑零修改。

### alembic 更新

`backend/alembic/env.py` 中的 `Base` 导入需从：
```python
from app.models import Base
```
改为：
```python
from notebooklm_shared.models import Base
```

---

## 迁移执行顺序

| 阶段 | 内容 | 风险 |
|------|------|------|
| 1 | 创建 `shared/` 包，迁移 config/database/models/auth | 低：新增代码 |
| 2 | 更新主 `backend/` import，验证主项目正常启动 | 中：import 遗漏会立即报错 |
| 3 | 构建 `admin/backend/`，迁移 admin router + auth login | 低：主要是迁移 |
| 4 | 构建 `admin/frontend/`，精简主前端 Vue 应用 | 低：UI 层迁移 |
| 5 | Docker Compose 端到端测试 | 低：网络配置 |

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 主 backend import 替换遗漏 | 阶段 2 启动检查，import 错误立即暴露 |
| shared/ 循环依赖 | shared 只引用第三方库，强制约束 |
| Docker 网络不存在 | README 注明前提：先启动 middleware |
| alembic Base 路径未更新 | 阶段 2 checklist 包含此项 |
| admin 前端缺少 i18n | 按需迁移 `src/i18n/` 和 `src/locales/` |
