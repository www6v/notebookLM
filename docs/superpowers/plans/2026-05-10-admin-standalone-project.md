# Admin 独立部署项目 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 admin 功能从 notebookLM 主项目提取到 `admin/` 目录，形成可通过 `docker-compose up` 独立部署的前后端项目，共享同一 MySQL 数据库。

**Architecture:** 创建 `shared/` Python 包（`notebooklm-shared`）存放 config/database/models/auth 核心代码；主 `backend/` 批量替换 import 路径；`admin/backend/` 为轻量 FastAPI 应用只含 admin + auth 路由；`admin/frontend/` 为仅含 admin 页面的 Vue 3 应用；两者通过 `admin/docker-compose.yml` 挂载到已有 Docker 网络统一部署。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy async, uv, pytest; Vue 3, Vite, Vuetify 3, TypeScript, axios; Docker + nginx

---

## File Map

### 新建文件

```
shared/
  pyproject.toml
  notebooklm_shared/__init__.py
  notebooklm_shared/config.py          ← 从 backend/app/config.py 迁移
  notebooklm_shared/database.py        ← 从 backend/app/database.py 迁移
  notebooklm_shared/models/__init__.py ← 从 backend/app/models/__init__.py 迁移
  notebooklm_shared/models/user.py     ← 从 backend/app/models/user.py 迁移
  notebooklm_shared/models/notebook.py
  notebooklm_shared/models/source.py
  notebooklm_shared/models/chat.py
  notebooklm_shared/models/note.py
  notebooklm_shared/models/studio.py
  notebooklm_shared/models/user_settings.py
  notebooklm_shared/models/payment.py
  notebooklm_shared/models/system_setting.py
  notebooklm_shared/models/featured_notebook_link.py
  notebooklm_shared/auth/__init__.py
  notebooklm_shared/auth/service.py    ← 从 backend/app/services/security/auth_service.py 迁移
  tests/__init__.py
  tests/test_imports.py
  tests/test_jwt.py

admin/backend/
  pyproject.toml
  app/__init__.py
  app/main.py
  app/api/__init__.py
  app/api/admin.py                     ← 从 backend/app/api/admin.py 迁移
  app/api/auth.py                      ← 从 backend/app/api/auth.py 精简
  app/api/deps.py                      ← 从 backend/app/api/deps.py 迁移
  app/schemas/__init__.py
  app/schemas/user.py                  ← 从 backend/app/schemas/user.py 复制
  app/schemas/client_config.py
  app/schemas/featured_notebook.py
  app/services/__init__.py
  app/services/system_setting_service.py ← 从 backend 复制
  app/services/featured_notebook_service.py
  config.yaml.example
  .env.example
  Dockerfile
  tests/__init__.py
  tests/test_health.py
  tests/test_auth.py

admin/frontend/
  package.json
  vite.config.ts
  tsconfig.json
  tsconfig.node.json
  index.html
  postcss.config.cjs
  src/main.ts
  src/App.vue
  src/router/index.ts
  src/stores/useUserStore.ts
  src/api/client.ts
  src/api/auth.ts
  src/api/admin.ts
  src/views/LoginPage.vue              ← 从 frontend 迁移
  src/views/admin/AdminUserList.vue
  src/views/admin/AdminUserDetail.vue
  src/views/admin/AdminFeaturedNotebooksPage.vue
  src/views/admin/AdminDesktopPage.vue
  nginx.conf
  Dockerfile

admin/
  docker-compose.yml
  README.md
```

### 修改文件

```
backend/pyproject.toml                 ← 新增 notebooklm-shared 依赖
backend/alembic/env.py                 ← 更新 Base + models 导入路径
backend/app/**/*.py (~183处)           ← 批量替换 import 路径
```

### 删除文件（迁移后）

```
backend/app/config.py
backend/app/database.py
backend/app/models/（整个目录）
backend/app/services/security/auth_service.py
```

---

## Task 1: 创建 shared/ 包骨架

**Files:**
- Create: `shared/pyproject.toml`
- Create: `shared/notebooklm_shared/__init__.py`
- Create: `shared/tests/__init__.py`
- Create: `shared/tests/test_imports.py`

- [ ] **Step 1: 写 shared/pyproject.toml**

```toml
[project]
name = "notebooklm-shared"
version = "0.1.0"
description = "Shared models, config, and auth for notebookLM services"
requires-python = ">=3.10"
dependencies = [
    "sqlalchemy[asyncio]>=2.0.36",
    "aiomysql>=0.2.0",
    "python-jose[cryptography]>=3.3.0",
    "bcrypt>=4.0.0",
    "pydantic-settings>=2.7.0",
    "pyyaml>=6.0.1",
    "python-dotenv>=1.0.1",
    "cryptography>=42.0.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: 创建包入口**

创建 `shared/notebooklm_shared/__init__.py`（空文件）。

创建 `shared/tests/__init__.py`（空文件）。

- [ ] **Step 3: 写占位测试**

`shared/tests/test_imports.py`:
```python
def test_package_importable():
    import notebooklm_shared
    assert notebooklm_shared is not None
```

- [ ] **Step 4: 安装并运行测试确认 PASS**

```bash
cd shared
uv sync
uv run pytest tests/test_imports.py -v
```

预期输出：`PASSED`

- [ ] **Step 5: Commit**

```bash
git add shared/
git commit -m "feat(shared): create notebooklm-shared package scaffold"
```

---

## Task 2: 迁移 config.py 到 shared/

**Files:**
- Create: `shared/notebooklm_shared/config.py`

- [ ] **Step 1: 复制 config.py 到 shared/ 并更新**

将 `backend/app/config.py` 内容复制到 `shared/notebooklm_shared/config.py`。

修改其中的 `_repo_root()` 函数——添加对 `shared/` 目录结构的支持（原函数检查 `backend/app` 是否存在，已能正确找到 monorepo 根目录，无需改动逻辑，但添加注释说明）：

```python
def _repo_root() -> Path:
    """Directory for config.yaml and optional .env.

    When called from notebooklm_shared (shared/notebooklm_shared/config.py):
    - here = .../notebookLM/shared/notebooklm_shared/config.py
    - monorepo_candidate = .../notebookLM/
    - Check: notebookLM/backend/app exists → returns notebookLM/ ✓

    In Docker (admin/backend), set NOTEBOOKLM_CONFIG_PATH=/app/config.yaml
    to bypass this discovery logic.
    """
    here = Path(__file__).resolve()
    backend_app = here.parent        # notebooklm_shared/
    backend_root = backend_app.parent  # shared/
    monorepo_candidate = backend_root.parent  # notebookLM/
    if (monorepo_candidate / "backend" / "app").is_dir():
        return monorepo_candidate
    return backend_root
```

内容完全相同，仅更新注释。

- [ ] **Step 2: 写 import 测试**

在 `shared/tests/test_imports.py` 追加：
```python
def test_settings_importable():
    from notebooklm_shared.config import settings
    assert settings is not None
    assert hasattr(settings, 'database_url')
```

- [ ] **Step 3: 运行测试（预期 PASS，前提 config.yaml 存在于 notebookLM/）**

```bash
cd shared
uv run pytest tests/test_imports.py::test_settings_importable -v
```

预期：`PASSED`（若 config.yaml 不存在会 SKIP，属正常）

- [ ] **Step 4: Commit**

```bash
git add shared/notebooklm_shared/config.py shared/tests/
git commit -m "feat(shared): migrate config.py to notebooklm_shared"
```

---

## Task 3: 迁移 database.py 和 models/ 到 shared/

**Files:**
- Create: `shared/notebooklm_shared/database.py`
- Create: `shared/notebooklm_shared/models/` (所有 .py)
- Create: `shared/tests/test_models.py`

- [ ] **Step 1: 复制 database.py 到 shared/ 并更新 import**

将 `backend/app/database.py` 复制到 `shared/notebooklm_shared/database.py`，修改顶部 import：

```python
# 修改前：from app.config import settings
# 修改后：
from notebooklm_shared.config import settings
```

修改 `init_db()` 中的 model imports：

```python
async def init_db():
    """Initialize all database tables."""
    from notebooklm_shared.models import (  # noqa: F401
        user,
        notebook,
        source,
        chat,
        note,
        studio,
        user_settings,
        payment,
        system_setting,
        featured_notebook_link,
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database tables: {e}")
        raise
```

- [ ] **Step 2: 复制所有 model 文件并更新 imports**

将 `backend/app/models/` 下所有 `.py` 文件复制到 `shared/notebooklm_shared/models/`。

对每个 model 文件，将 import 前缀从 `app.` 改为 `notebooklm_shared.`：

```bash
cd shared/notebooklm_shared/models
# 每个文件中的 from app.database 改为 from notebooklm_shared.database
sed -i '' 's/from app\.database/from notebooklm_shared.database/g' *.py
sed -i '' 's/from app\.models/from notebooklm_shared.models/g' *.py
sed -i '' 's/from app\.config/from notebooklm_shared.config/g' *.py
```

- [ ] **Step 3: 创建 models/__init__.py**

`shared/notebooklm_shared/models/__init__.py`:
```python
from notebooklm_shared.models.user import User
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.source import Source
from notebooklm_shared.models.chat import ChatSession, Message
from notebooklm_shared.models.note import Note
from notebooklm_shared.models.studio import MindMap, SlideDeck, Infographic, Report, PodcastOverview
from notebooklm_shared.models.user_settings import UserSettings
from notebooklm_shared.models.payment import PaymentOrder
from notebooklm_shared.models.system_setting import SystemSetting
from notebooklm_shared.models.featured_notebook_link import FeaturedNotebookLink

__all__ = [
    "User", "Notebook", "Source", "ChatSession", "Message", "Note",
    "MindMap", "SlideDeck", "Infographic", "Report", "PodcastOverview",
    "UserSettings", "PaymentOrder", "SystemSetting", "FeaturedNotebookLink",
]
```

- [ ] **Step 4: 写 model import 测试**

`shared/tests/test_models.py`:
```python
def test_user_model_importable():
    from notebooklm_shared.models.user import User
    assert User.__tablename__ is not None

def test_all_models_importable():
    from notebooklm_shared.models import (
        User, Notebook, Source, SystemSetting, FeaturedNotebookLink
    )
    assert User is not None
    assert Notebook is not None

def test_base_has_metadata():
    from notebooklm_shared.database import Base
    assert Base.metadata is not None
```

- [ ] **Step 5: 运行测试**

```bash
cd shared
uv run pytest tests/test_models.py -v
```

预期：3 个 `PASSED`

- [ ] **Step 6: Commit**

```bash
git add shared/notebooklm_shared/database.py shared/notebooklm_shared/models/ shared/tests/test_models.py
git commit -m "feat(shared): migrate database.py and models to notebooklm_shared"
```

---

## Task 4: 迁移 auth service 到 shared/

**Files:**
- Create: `shared/notebooklm_shared/auth/__init__.py`
- Create: `shared/notebooklm_shared/auth/service.py`
- Create: `shared/tests/test_jwt.py`

- [ ] **Step 1: 复制 auth_service.py 到 shared/ 并更新 imports**

将 `backend/app/services/security/auth_service.py` 复制到 `shared/notebooklm_shared/auth/service.py`，修改 imports：

```python
"""Authentication service: password hashing, JWT creation/verification."""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.config import settings   # 修改
from notebooklm_shared.models.user import User  # 修改

ALGORITHM = 'HS256'

# 以下函数定义保持完全不变：
# hash_password, verify_password, create_access_token, decode_access_token,
# get_user_by_email, get_user_by_username, get_user_by_id,
# create_user, authenticate_user
```

- [ ] **Step 2: 创建 auth/__init__.py**

`shared/notebooklm_shared/auth/__init__.py`（空文件）。

- [ ] **Step 3: 写 JWT 单元测试**

`shared/tests/test_jwt.py`:
```python
import os
os.environ.setdefault("NOTEBOOKLM_CONFIG_PATH", "/dev/null")

import pytest
from unittest.mock import patch, MagicMock

# Patch settings before import
mock_settings = MagicMock()
mock_settings.secret_key = "test-secret-key-for-unit-tests"
mock_settings.access_token_expire_minutes = 60

with patch("notebooklm_shared.config.settings", mock_settings):
    from notebooklm_shared.auth import service as auth_svc
    auth_svc.settings = mock_settings


def test_hash_and_verify_password():
    hashed = auth_svc.hash_password("mypassword123")
    assert hashed != "mypassword123"
    assert auth_svc.verify_password("mypassword123", hashed)
    assert not auth_svc.verify_password("wrongpassword", hashed)


def test_create_and_decode_token():
    token = auth_svc.create_access_token({"sub": "user-abc-123"})
    assert isinstance(token, str)
    payload = auth_svc.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-abc-123"


def test_decode_invalid_token_returns_none():
    result = auth_svc.decode_access_token("not.a.valid.token")
    assert result is None
```

- [ ] **Step 4: 运行测试**

```bash
cd shared
uv run pytest tests/test_jwt.py -v
```

预期：3 个 `PASSED`

- [ ] **Step 5: Commit**

```bash
git add shared/notebooklm_shared/auth/ shared/tests/test_jwt.py
git commit -m "feat(shared): migrate auth service (JWT + password) to notebooklm_shared"
```

---

## Task 5: 更新主 backend 使用 shared/ 包

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/**/*.py` (批量 import 替换)
- Delete: `backend/app/config.py`, `backend/app/database.py`, `backend/app/models/`, `backend/app/services/security/auth_service.py`

- [ ] **Step 1: 在 backend/pyproject.toml 添加 shared 依赖**

在 `backend/pyproject.toml` 的 `[project]` `dependencies` 数组添加一行（在列表末尾、`]` 前）：

```toml
    "notebooklm-shared @ ../shared",
```

- [ ] **Step 2: 安装依赖**

```bash
cd backend
uv sync
```

- [ ] **Step 3: 批量替换 import 路径**

```bash
cd backend/app

# config
find . -name "*.py" ! -path "*/__pycache__/*" \
  -exec sed -i '' 's/from app\.config import/from notebooklm_shared.config import/g' {} +

# database
find . -name "*.py" ! -path "*/__pycache__/*" \
  -exec sed -i '' 's/from app\.database import/from notebooklm_shared.database import/g' {} +

# models
find . -name "*.py" ! -path "*/__pycache__/*" \
  -exec sed -i '' 's/from app\.models\./from notebooklm_shared.models./g' {} +

# auth_service
find . -name "*.py" ! -path "*/__pycache__/*" \
  -exec sed -i '' 's/from app\.services\.security\.auth_service import/from notebooklm_shared.auth.service import/g' {} +
```

- [ ] **Step 4: 删除已迁移文件**

```bash
rm backend/app/config.py
rm backend/app/database.py
rm -rf backend/app/models/
rm backend/app/services/security/auth_service.py
```

- [ ] **Step 5: 验证主 backend 可启动（import 检查）**

```bash
cd backend
uv run python -c "from app.main import app; print('OK:', app.title)"
```

预期输出包含 `OK:`。若有 ImportError 或 ModuleNotFoundError，根据报错逐一修复遗漏的 import 替换。

- [ ] **Step 6: Commit**

```bash
cd ..  # back to notebookLM/
git add backend/
git commit -m "refactor(backend): use notebooklm_shared for config/database/models/auth"
```

---

## Task 6: 更新 alembic env.py

**Files:**
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: 更新 alembic/env.py 的 imports**

打开 `backend/alembic/env.py`，将前 30 行的 imports 改为：

```python
"""Alembic environment configuration for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from notebooklm_shared.config import settings
from notebooklm_shared.database import Base

# Import all models so they are registered with Base.metadata
from notebooklm_shared.models.user import User  # noqa: F401
from notebooklm_shared.models.notebook import Notebook  # noqa: F401
from notebooklm_shared.models.source import Source, SourceChunk  # noqa: F401
from notebooklm_shared.models.chat import ChatSession, Message  # noqa: F401
from notebooklm_shared.models.note import Note  # noqa: F401
from notebooklm_shared.models.studio import (  # noqa: F401
    DeepResearchReport,
    MindMap,
    Report,
    SlideDeck,
    Infographic,
)
from notebooklm_shared.models.payment import PaymentOrder  # noqa: F401
```

- [ ] **Step 2: 验证 alembic 可运行**

```bash
cd backend
uv run alembic current
```

预期：显示当前 migration 版本（无报错）

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/env.py
git commit -m "fix(backend): update alembic env.py to use notebooklm_shared"
```

---

## Task 7: 创建 admin/backend/ 骨架 + health 端点

**Files:**
- Create: `admin/backend/pyproject.toml`
- Create: `admin/backend/app/__init__.py`
- Create: `admin/backend/app/main.py`
- Create: `admin/backend/tests/__init__.py`
- Create: `admin/backend/tests/test_health.py`

- [ ] **Step 1: 写 admin/backend/pyproject.toml**

```toml
[project]
name = "notebooklm-admin-backend"
version = "0.1.0"
description = "Admin backend for notebookLM"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "email-validator>=2.1.0",
    "python-multipart>=0.0.18",
    "notebooklm-shared @ ../../shared",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

- [ ] **Step 2: 写 app/main.py（只含 health 端点）**

`admin/backend/app/main.py`:
```python
"""Admin backend FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NotebookLM Admin", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 3: 写 health 测试（先写，验证失败）**

`admin/backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: 安装依赖并运行测试**

```bash
cd admin/backend
uv sync
uv run pytest tests/test_health.py -v
```

预期：`PASSED`

- [ ] **Step 5: Commit**

```bash
git add admin/backend/
git commit -m "feat(admin/backend): scaffold FastAPI app with health endpoint"
```

---

## Task 8: 复制 admin 专属的 schemas 和 services

**Files:**
- Create: `admin/backend/app/schemas/__init__.py`
- Create: `admin/backend/app/schemas/user.py`
- Create: `admin/backend/app/schemas/client_config.py`
- Create: `admin/backend/app/schemas/featured_notebook.py`
- Create: `admin/backend/app/services/__init__.py`
- Create: `admin/backend/app/services/system_setting_service.py`
- Create: `admin/backend/app/services/featured_notebook_service.py`

- [ ] **Step 1: 复制 schemas 文件**

将以下文件原样复制（import 路径不含 `app.`，只依赖 pydantic，无需修改）：

```bash
cp backend/app/schemas/user.py admin/backend/app/schemas/user.py
cp backend/app/schemas/client_config.py admin/backend/app/schemas/client_config.py
cp backend/app/schemas/featured_notebook.py admin/backend/app/schemas/featured_notebook.py
```

创建 `admin/backend/app/schemas/__init__.py`（空文件）。

- [ ] **Step 2: 复制 system_setting_service.py 并更新 imports**

将 `backend/app/services/system_setting_service.py` 复制到 `admin/backend/app/services/system_setting_service.py`，将 import 改为：

```python
from notebooklm_shared.models.system_setting import SystemSetting
```

（原来是 `from app.models.system_setting import SystemSetting`）

- [ ] **Step 3: 复制 featured_notebook_service.py 并更新 imports**

将 `backend/app/services/featured_notebook_service.py` 复制到 `admin/backend/app/services/featured_notebook_service.py`，更新 imports：

```python
from notebooklm_shared.models.featured_notebook_link import FeaturedNotebookLink
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.source import Source
from app.schemas.featured_notebook import (
    FeaturedNotebookAdminItem,
    FeaturedNotebookEntryInput,
    FeaturedNotebookPublicItem,
)
```

创建 `admin/backend/app/services/__init__.py`（空文件）。

- [ ] **Step 4: 验证 schemas 可 import**

```bash
cd admin/backend
uv run python -c "from app.schemas.user import AdminUserListResponse; print('OK')"
uv run python -c "from app.schemas.featured_notebook import FeaturedNotebooksAdminListResponse; print('OK')"
```

预期：两行均输出 `OK`

- [ ] **Step 5: Commit**

```bash
git add admin/backend/app/schemas/ admin/backend/app/services/
git commit -m "feat(admin/backend): add admin-specific schemas and services"
```

---

## Task 9: 实现 admin/backend/ API（deps + admin router + auth router）

**Files:**
- Create: `admin/backend/app/api/__init__.py`
- Create: `admin/backend/app/api/deps.py`
- Create: `admin/backend/app/api/auth.py`
- Create: `admin/backend/app/api/admin.py`
- Modify: `admin/backend/app/main.py`
- Create: `admin/backend/tests/test_auth.py`

- [ ] **Step 1: 写 app/api/deps.py**

`admin/backend/app/api/deps.py`:
```python
"""FastAPI dependencies for admin backend."""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from notebooklm_shared.models.user import User
from notebooklm_shared.auth.service import decode_access_token, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    if (
        user.role == "paid"
        and user.subscription_expires_at is not None
        and user.subscription_expires_at < datetime.now(timezone.utc)
    ):
        user.role = "free"
        user.subscription_plan = "free"
        db.add(user)
        await db.flush()
    return user


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
```

- [ ] **Step 2: 写 app/api/auth.py（login + me 端点）**

`admin/backend/app/api/auth.py`:
```python
"""Auth endpoints for admin login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from notebooklm_shared.auth.service import authenticate_user, create_access_token
from app.api.deps import get_current_user
from app.schemas.user import Token, UserLogin, UserResponse
from notebooklm_shared.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate admin user and return JWT token."""
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
```

- [ ] **Step 3: 复制 admin router 并更新 imports**

将 `backend/app/api/admin.py` 复制到 `admin/backend/app/api/admin.py`，更新所有 imports：

```python
"""Admin API routes for user management."""

from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from notebooklm_shared.database import get_db
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.source import Source
from notebooklm_shared.models.studio import (
    Infographic,
    MindMap,
    PodcastOverview,
    Report,
    SlideDeck,
)
from notebooklm_shared.models.user import User
from app.schemas.client_config import (
    AdminClientConfigUpdate,
    PublicClientConfigResponse,
)
from app.schemas.featured_notebook import (
    FeaturedNotebooksAdminListResponse,
    FeaturedNotebooksReplaceRequest,
)
from app.schemas.user import (
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserUpdateRequest,
    NotebookStatsItem,
    UploadedFileTypeStat,
    UserResponse,
)
from app.services import featured_notebook_service as featured_svc
from app.services import system_setting_service as sys_svc

router = APIRouter(prefix="/api/admin", tags=["admin"])
```

其余函数体（`_normalize_desktop_backend_url`、`_count_studio_ready_error`、所有 endpoint 函数）原样保留不变。

- [ ] **Step 4: 在 main.py 注册 routers**

更新 `admin/backend/app/main.py`：
```python
"""Admin backend FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth

app = FastAPI(title="NotebookLM Admin", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 写 auth 端点测试（mock DB）**

`admin/backend/tests/test_auth.py`:
```python
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def make_mock_user(role="admin", is_active=True):
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "admin@test.com"
    user.username = "admin"
    user.role = role
    user.is_active = is_active
    user.subscription_expires_at = None
    user.subscription_plan = "free"
    user.created_at = "2024-01-01T00:00:00"
    return user


def test_login_non_admin_returns_403():
    with patch("app.api.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = make_mock_user(role="free")
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            json={"email": "user@test.com", "password": "password"},
        )
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_login_invalid_credentials_returns_401():
    with patch("app.api.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = None
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "wrong"},
        )
    assert response.status_code == 401
```

- [ ] **Step 6: 运行所有 admin/backend 测试**

```bash
cd admin/backend
uv run pytest tests/ -v
```

预期：`test_health_returns_ok` PASSED，`test_login_non_admin_returns_403` PASSED，`test_login_invalid_credentials_returns_401` PASSED

- [ ] **Step 7: Commit**

```bash
git add admin/backend/app/api/ admin/backend/app/main.py admin/backend/tests/
git commit -m "feat(admin/backend): implement admin + auth API endpoints"
```

---

## Task 10: 创建 admin/backend/ 配置文件和 Dockerfile

**Files:**
- Create: `admin/backend/config.yaml.example`
- Create: `admin/backend/.env.example`
- Create: `admin/backend/Dockerfile`

- [ ] **Step 1: 写 config.yaml.example**

`admin/backend/config.yaml.example`:
```yaml
# Admin backend configuration
# Copy to config.yaml and fill in values, or use NOTEBOOKLM_CONFIG_PATH env var

database:
  host: "localhost"
  port: 3306
  name: "notebooklm"
  user: "root"
  password: "${DB_PASSWORD}"
  pool_size: 5
  max_overflow: 10
  pool_timeout_seconds: 30
  pool_recycle_seconds: 1800

redis:
  host: "localhost"
  port: 6379
  db: 0

application:
  debug: false
  secret_key: "${SECRET_KEY}"
  access_token_expire_minutes: 1440
```

- [ ] **Step 2: 写 .env.example**

`admin/backend/.env.example`:
```
# Copy to .env and fill in secrets
DB_PASSWORD=your_database_password_here
SECRET_KEY=your_jwt_secret_key_here_min_32_chars
```

- [ ] **Step 3: 写 Dockerfile**

`admin/backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

# Install shared package first (for layer caching)
COPY ../../shared /shared
RUN uv pip install --system /shared

# Install admin backend
COPY pyproject.toml .
RUN uv pip install --system -e .

COPY . .

# Tell config.py where to find config.yaml (mounted by docker-compose)
ENV NOTEBOOKLM_CONFIG_PATH=/app/config.yaml

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> **注意：** Dockerfile 中 `COPY ../../shared /shared` 需要从 `admin/` 目录执行 `docker build` 以获得正确的 build context，见 docker-compose.yml 的 `context` 配置。

- [ ] **Step 4: Commit**

```bash
git add admin/backend/config.yaml.example admin/backend/.env.example admin/backend/Dockerfile
git commit -m "feat(admin/backend): add config, env example, and Dockerfile"
```

---

## Task 11: 创建 admin/frontend/ Vue 项目骨架

**Files:**
- Create: `admin/frontend/package.json`
- Create: `admin/frontend/vite.config.ts`
- Create: `admin/frontend/tsconfig.json`
- Create: `admin/frontend/tsconfig.node.json`
- Create: `admin/frontend/index.html`
- Create: `admin/frontend/postcss.config.cjs`
- Create: `admin/frontend/src/main.ts`
- Create: `admin/frontend/src/App.vue`

- [ ] **Step 1: 写 package.json**

`admin/frontend/package.json`:
```json
{
  "name": "notebooklm-admin-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@mdi/font": "^7.4.47",
    "axios": "^1.7.9",
    "pinia": "^2.3.0",
    "vue": "^3.5.13",
    "vue-router": "^4.5.0",
    "vuetify": "^3.12.3",
    "vite-plugin-vuetify": "^2.1.3"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.1",
    "autoprefixer": "^10.4.27",
    "cssnano": "^7.1.3",
    "postcss": "^8.5.8",
    "sass": "^1.83.0",
    "typescript": "~5.7.2",
    "vite": "^6.0.5",
    "vue-tsc": "^2.2.0"
  }
}
```

- [ ] **Step 2: 写 vite.config.ts**

`admin/frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: 写 tsconfig.json 和 tsconfig.node.json**

`admin/frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`admin/frontend/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: 写 index.html**

`admin/frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NotebookLM Admin</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 5: 写 src/App.vue**

`admin/frontend/src/App.vue`:
```vue
<template>
  <v-app>
    <router-view />
  </v-app>
</template>
```

- [ ] **Step 6: 写 src/main.ts**

`admin/frontend/src/main.ts`:
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import App from './App.vue'
import router from './router'

const vuetify = createVuetify({ components, directives })

createApp(App)
  .use(createPinia())
  .use(router)
  .use(vuetify)
  .mount('#app')
```

- [ ] **Step 7: 写 postcss.config.cjs**

`admin/frontend/postcss.config.cjs`:
```javascript
module.exports = {
  plugins: {
    autoprefixer: {},
    cssnano: {},
  },
}
```

- [ ] **Step 8: 安装依赖并验证构建**

```bash
cd admin/frontend
npm install
npm run build
```

预期：`dist/` 目录生成，无 TypeScript 报错

- [ ] **Step 9: Commit**

```bash
git add admin/frontend/package.json admin/frontend/vite.config.ts admin/frontend/tsconfig*.json admin/frontend/index.html admin/frontend/postcss.config.cjs admin/frontend/src/
git commit -m "feat(admin/frontend): scaffold Vue 3 + Vite + Vuetify admin app"
```

---

## Task 12: 迁移 admin Vue 页面、router、store 和 API

**Files:**
- Create: `admin/frontend/src/api/client.ts`
- Create: `admin/frontend/src/api/auth.ts`
- Create: `admin/frontend/src/api/admin.ts`
- Create: `admin/frontend/src/stores/useUserStore.ts`
- Create: `admin/frontend/src/router/index.ts`
- Create: `admin/frontend/src/views/LoginPage.vue`
- Create: `admin/frontend/src/views/admin/AdminUserList.vue`
- Create: `admin/frontend/src/views/admin/AdminUserDetail.vue`
- Create: `admin/frontend/src/views/admin/AdminFeaturedNotebooksPage.vue`
- Create: `admin/frontend/src/views/admin/AdminDesktopPage.vue`

- [ ] **Step 1: 复制 API 文件**

```bash
cp frontend/src/api/client.ts admin/frontend/src/api/client.ts
cp frontend/src/api/auth.ts admin/frontend/src/api/auth.ts
cp frontend/src/api/admin.ts admin/frontend/src/api/admin.ts
```

修改 `admin/frontend/src/api/client.ts` 中的 401 处理（去掉 i18n locale 依赖，直接跳转 `/login`）：

```typescript
import axios from 'axios'
import { useUserStore } from '@/stores/useUserStore'
import router from '@/router'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default client
```

修改 `admin/frontend/src/api/admin.ts`：移除 `import type { PublicClientConfig } from '@/api/publicClient'` 这行，将 `PublicClientConfig` 类型内联定义：

```typescript
// 在文件顶部添加：
export interface PublicClientConfig {
  desktop_backend_url: string | null
}
```

- [ ] **Step 2: 复制 useUserStore**

```bash
cp frontend/src/stores/useUserStore.ts admin/frontend/src/stores/useUserStore.ts
```

修改 `logout()` 方法（去掉 i18n 重定向逻辑）：
```typescript
const logout = () => {
  const email = user.value?.email
  if (email) {
    localStorage.setItem(LAST_LOGIN_ACCOUNT_KEY, email)
  }
  clearToken()
}
```

（其余内容原样保留）

- [ ] **Step 3: 写 router/index.ts（只含 admin 路由）**

`admin/frontend/src/router/index.ts`:
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/useUserStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginPage.vue'),
    },
    {
      path: '/admin',
      name: 'AdminUserList',
      component: () => import('@/views/admin/AdminUserList.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/users/:id',
      name: 'AdminUserDetail',
      component: () => import('@/views/admin/AdminUserDetail.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/featured',
      name: 'AdminFeaturedNotebooks',
      component: () => import('@/views/admin/AdminFeaturedNotebooksPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/desktop',
      name: 'AdminDesktop',
      component: () => import('@/views/admin/AdminDesktopPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/',
      redirect: '/admin',
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/admin',
    },
  ],
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      return '/login'
    }
    if (!userStore.user) {
      await userStore.fetchUser()
    }
    if (to.meta.requiresAdmin && !userStore.isAdmin) {
      return '/login'
    }
  }
})

export default router
```

- [ ] **Step 4: 复制 admin Vue 页面**

```bash
cp frontend/src/views/LoginPage.vue admin/frontend/src/views/LoginPage.vue
cp frontend/src/views/admin/AdminUserList.vue admin/frontend/src/views/admin/AdminUserList.vue
cp frontend/src/views/admin/AdminUserDetail.vue admin/frontend/src/views/admin/AdminUserDetail.vue
cp frontend/src/views/admin/AdminFeaturedNotebooksPage.vue admin/frontend/src/views/admin/AdminFeaturedNotebooksPage.vue
cp frontend/src/views/admin/AdminDesktopPage.vue admin/frontend/src/views/admin/AdminDesktopPage.vue
```

检查 `LoginPage.vue`——如果它依赖 i18n 或 locale 路由（如 `router.push({ name: 'Login', params: { locale: ... } })`），将登录成功后的跳转改为：
```typescript
router.push('/admin')
```

- [ ] **Step 5: 验证 TypeScript 编译通过**

```bash
cd admin/frontend
npm run build
```

若有 TypeScript 报错，逐一修复（通常是 i18n 相关 import 或 locale 参数）。预期：`dist/` 生成，无报错。

- [ ] **Step 6: Commit**

```bash
git add admin/frontend/src/
git commit -m "feat(admin/frontend): migrate admin pages, router, store, and API"
```

---

## Task 13: 创建 admin/frontend/ nginx.conf 和 Dockerfile

**Files:**
- Create: `admin/frontend/nginx.conf`
- Create: `admin/frontend/Dockerfile`

- [ ] **Step 1: 写 nginx.conf**

`admin/frontend/nginx.conf`:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    sendfile off;
    tcp_nopush off;

    location /api/ {
        proxy_pass http://admin-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 2: 写 Dockerfile**

`admin/frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build


FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 3: 验证 Docker 镜像可构建**

```bash
cd admin/frontend
npm install  # 确保 package-lock.json 存在
docker build -t admin-frontend-test .
```

预期：`Successfully built ...`（或 `Successfully tagged ...`）

- [ ] **Step 4: Commit**

```bash
git add admin/frontend/nginx.conf admin/frontend/Dockerfile admin/frontend/package-lock.json
git commit -m "feat(admin/frontend): add nginx config and Dockerfile"
```

---

## Task 14: 创建 admin/ docker-compose.yml 和 README

**Files:**
- Create: `admin/docker-compose.yml`
- Create: `admin/README.md`

- [ ] **Step 1: 写 docker-compose.yml**

`admin/docker-compose.yml`:
```yaml
services:
  admin-backend:
    build:
      context: .          # admin/ 目录作为 build context
      dockerfile: backend/Dockerfile
    env_file: ./backend/.env
    volumes:
      - ./backend/config.yaml:/app/config.yaml:ro
    networks:
      - notebooklm_default
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  admin-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    depends_on:
      admin-backend:
        condition: service_healthy
    networks:
      - notebooklm_default

networks:
  notebooklm_default:
    external: true
```

> **重要：** `context: .`（admin/ 目录）让 Dockerfile 中的 `COPY ../../shared /shared` 改为 `COPY ../shared /shared`。

更新 `admin/backend/Dockerfile` 中的 shared 复制路径：

```dockerfile
# 将原来的：
COPY ../../shared /shared
# 改为（因为 build context 是 admin/）：
COPY ../shared /shared
```

- [ ] **Step 2: 写 README.md**

`admin/README.md`:
```markdown
# NotebookLM Admin

独立部署的后台管理系统，管理用户、精选笔记本和桌面端配置。

## 前提条件

1. 主项目的 middleware（MySQL、Redis）已通过 `make up-middleware` 启动
2. `notebooklm_default` Docker 网络已存在
3. `admin/backend/config.yaml` 已从 `config.yaml.example` 复制并填写

## 快速启动

```bash
# 1. 复制并填写配置
cp backend/config.yaml.example backend/config.yaml
cp backend/.env.example backend/.env
# 编辑 backend/.env 填写 DB_PASSWORD 和 SECRET_KEY

# 2. 启动（从 admin/ 目录执行）
docker compose up -d

# 3. 访问
open http://localhost:8080
```

## 配置说明

| 变量 | 说明 |
|------|------|
| `DB_PASSWORD` | MySQL 密码（与主项目相同） |
| `SECRET_KEY` | JWT 签名密钥（与主项目相同，保证 token 互通） |

`config.yaml` 中 `database.host` 在 Docker 内应填写 MySQL 容器名（如 `mysql`）。

## 端口

| 服务 | 端口 |
|------|------|
| admin-frontend（nginx） | 8080 |
| admin-backend（内部） | 8000（不对外暴露） |
```

- [ ] **Step 3: 端到端冒烟测试**

确保主项目 middleware 已启动，然后：

```bash
cd admin
cp backend/config.yaml.example backend/config.yaml
# 编辑 config.yaml 填写真实 DB 和 Redis 配置

docker compose build
docker compose up -d
```

等待健康检查通过（约 30 秒），然后：

```bash
# 验证 backend health
curl http://localhost:8080/api/health
# 预期：{"status":"ok"}

# 验证前端可访问
curl -I http://localhost:8080
# 预期：HTTP/1.1 200 OK
```

打开浏览器访问 `http://localhost:8080`，确认：
- 重定向到 `/login`
- 用 admin 账号登录后跳转到 `/admin` 用户列表页
- 用户列表正常加载

- [ ] **Step 4: Commit**

```bash
git add admin/docker-compose.yml admin/README.md admin/backend/Dockerfile
git commit -m "feat(admin): add docker-compose.yml and deployment README"
```

---

## Self-Review Checklist

经过规格检查：

| 规格要求 | 对应任务 |
|---------|---------|
| shared/ 包含 config/database/models/auth | Task 1-4 |
| 主 backend 更新 import + alembic | Task 5-6 |
| admin/backend/ 独立 FastAPI，只含 admin+auth 路由 | Task 7-9 |
| admin/backend/ Dockerfile + 配置示例 | Task 10 |
| admin/frontend/ Vue 3 骨架 | Task 11 |
| 迁移 4 个 admin 页面 + LoginPage | Task 12 |
| admin/frontend/ nginx + Dockerfile | Task 13 |
| docker-compose 挂载外部网络 | Task 14 |
| SECRET_KEY 说明（保证 token 互通） | Task 14 README |
| alembic 路径更新 | Task 6 |
