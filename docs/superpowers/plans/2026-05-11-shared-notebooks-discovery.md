# 共享笔记本、发现与订阅 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现设计 spec `docs/superpowers/specs/2026-05-11-shared-notebooks-discovery-design.md`：上架到发现、公开发现列表/详情、登录订阅与退订、首页笔记本列表区水平三 Tab、顶栏「发现」页（搜索/精选/分类/卡片），订阅者只读体验 MVP 通过既有 `share_token` 只读链路打开笔记本。

**Architecture:** 采用 `notebook_discover_profiles`（上架元数据）与 `notebook_subscriptions`（订阅关系）两张新表；上架接口挂在现有 `notebooks` 路由；匿名可读放在 `/api/public/discover/*`（与 `public_config` 一致）；订阅动作放在 `/api/discover/*` 需 JWT。列表接口为 `GET /api/notebooks/published` 与 `GET /api/notebooks/subscriptions`（不破坏现有 `GET /api/notebooks` 全量自有本语义）。打开已订阅本：MVP 使用 `/shared/:shareToken`（要求上架时确保 `share_token` 存在）。

**Tech Stack:** FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, pytest, httpx；Vue 3, Pinia, Vue Router, Vuetify, TypeScript。

---

## File map

### 新建（后端）

| 文件 | 职责 |
|------|------|
| `shared/notebooklm_shared/models/notebook_discover_profile.py` | 上架元数据 ORM |
| `shared/notebooklm_shared/models/notebook_subscription.py` | 订阅 ORM |
| `backend/alembic/versions/20260511_discover_subscribe.py` | DDL：两表 + 索引 |
| `backend/app/schemas/discover.py` | 发现列表/详情、上架 body DTO |
| `backend/app/services/discover_service.py` | 查询、上架、计数维护 |
| `backend/app/api/public_discover.py` | `GET /api/public/discover/notebooks`、`GET .../{id}` |
| `backend/app/api/discover.py` | `POST/DELETE /api/discover/notebooks/{id}/subscribe` |
| `backend/tests/test_discover_api.py` | API 与权限测试 |

### 修改（后端）

| 文件 | 职责 |
|------|------|
| `shared/notebooklm_shared/models/notebook.py` | `relationship` 到 profile / subscriptions（可选） |
| `shared/notebooklm_shared/models/__init__.py` | export 新模型 |
| `shared/notebooklm_shared/database.py` | `init_db` import 新模型模块 |
| `backend/app/api/notebooks.py` | `POST/DELETE .../{id}/discover/publish`；必要时 `enable_or_rotate` 与上架联动 |
| `backend/app/main.py` | `include_router` public_discover、discover |

### 新建（前端）

| 文件 | 职责 |
|------|------|
| `frontend/src/views/DiscoverPage.vue` | 发现页布局 |
| `frontend/src/api/discover.ts` | public list/detail、subscribe API |
| `frontend/src/components/discover/DiscoverNotebookCard.vue` | 卡片（多词组件名） |

### 修改（前端）

| 文件 | 职责 |
|------|------|
| `frontend/src/router/index.ts` | 路由 `discover`，`meta.requiresAuth: false`（列表匿名可浏览） |
| `frontend/src/views/HomePage.vue` | 顶栏「发现」按钮；`mine` 区域内水平三 Tab + 三套数据拉取 |
| `frontend/src/api/notebook.ts` | `listPublished`、`listSubscriptions` 类型与调用 |
| `frontend/src/stores/useNotebookStore.ts` | `publishedNotebooks`、`subscribedNotebooks` 或专用 fetch 方法 |
| `frontend/src/locales/zh-CN.ts`、`en.ts` | 文案键 |

### 不改（MVP）

- `admin/` 强制下架（spec Phase 2）。
- 订阅者免 token 的「身份只读」统一 API（可作为后续任务）。

---

## Task 1: 共享模型与 Alembic

**Files:**

- Create: `shared/notebooklm_shared/models/notebook_discover_profile.py`
- Create: `shared/notebooklm_shared/models/notebook_subscription.py`
- Create: `backend/alembic/versions/20260511_discover_subscribe.py`
- Modify: `shared/notebooklm_shared/models/__init__.py`
- Modify: `shared/notebooklm_shared/database.py`

- [ ] **Step 1: 新增 `NotebookDiscoverProfile`**

```python
# shared/notebooklm_shared/models/notebook_discover_profile.py
"""Discover catalog metadata for a notebook (owner-published)."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin


class NotebookDiscoverProfile(Base, TimestampMixin):
    __tablename__ = "notebook_discover_profiles"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id", ondelete="CASCADE"), primary_key=True
    )
    category: Mapped[str] = mapped_column(String(64), default="general", nullable=False)
    cover_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    notebook = relationship("Notebook", back_populates="discover_profile")
```

- [ ] **Step 2: 新增 `NotebookSubscription`**

```python
# shared/notebooklm_shared/models/notebook_subscription.py
"""User subscription to another user's discoverable notebook."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin, UUIDMixin


class NotebookSubscription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notebook_subscriptions"
    __table_args__ = (
        UniqueConstraint("subscriber_user_id", "notebook_id", name="uq_sub_notebook"),
    )

    subscriber_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )

    subscriber = relationship("User", foreign_keys=[subscriber_user_id])
    notebook = relationship("Notebook", foreign_keys=[notebook_id])
```

- [ ] **Step 3: 在 `Notebook` 上增加 `relationship`**

在 `shared/notebooklm_shared/models/notebook.py` 末尾增加（名称与 Step 1 `back_populates` 一致）：

```python
    discover_profile = relationship(
        "NotebookDiscoverProfile",
        back_populates="notebook",
        uselist=False,
        cascade="all, delete-orphan",
    )
```

（若 `NotebookSubscription` 需从 Notebook 导航，可加 `subscriptions` relationship；非必须。）

- [ ] **Step 4: `models/__init__.py` 与 `database.py`**

- 在 `__init__.py` 导入并加入 `__all__`：`NotebookDiscoverProfile`, `NotebookSubscription`。
- 在 `database.py` 的 `init_db` 内联 import 元组中增加 `notebook_discover_profile`, `notebook_subscription`（与现有风格一致）。

- [ ] **Step 5: Alembic 迁移**

新建 revision：`20260511_discover_subscribe.py`，`upgrade()`：

- `notebook_discover_profiles`：`notebook_id` PK FK `notebooks.id` ON DELETE CASCADE，`category`、`cover_url`、`subscriber_count`、`created_at`、`updated_at`（与 `TimestampMixin` 列名一致）。
- `notebook_subscriptions`：`id` PK，`subscriber_user_id` FK `users.id` ON DELETE CASCADE，`notebook_id` FK `notebooks.id` ON DELETE CASCADE，`created_at`、`updated_at`，唯一索引 `(subscriber_user_id, notebook_id)`。

`downgrade()` 删除两表。

- [ ] **Step 6: 本地执行迁移**

```bash
cd backend && uv run alembic upgrade head
```

Expected: 无报错；MySQL/SQLite 与项目当前配置一致。

- [ ] **Step 7: Commit**

```bash
git add shared/notebooklm_shared/models/ backend/alembic/versions/20260511_discover_subscribe.py shared/notebooklm_shared/database.py shared/notebooklm_shared/models/__init__.py shared/notebooklm_shared/models/notebook.py
git commit -m "feat(db): discover profiles and notebook subscriptions"
```

---

## Task 2: Schemas

**Files:**

- Create: `backend/app/schemas/discover.py`

- [ ] **定义 DTO**（字段名与前端对齐，示例）

```python
# backend/app/schemas/discover.py
from pydantic import BaseModel, Field


class DiscoverPublishBody(BaseModel):
    category: str = Field(default="general", max_length=64)
    cover_url: str = Field(default="", max_length=512)


class DiscoverNotebookListItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    cover_url: str
    subscriber_count: int
    source_count: int
    owner_display_name: str


class DiscoverNotebookListResponse(BaseModel):
    items: list[DiscoverNotebookListItem]
    total: int


class DiscoverNotebookDetail(BaseModel):
    id: str
    title: str
    description: str
    category: str
    cover_url: str
    subscriber_count: int
    source_count: int
    owner_display_name: str
    share_token: str | None
```

（`owner_display_name` 从 `User` 昵称/email 派生；实现服务层拼接。）

- [ ] **Commit**

```bash
git add backend/app/schemas/discover.py
git commit -m "feat(api): discover pydantic schemas"
```

---

## Task 3: `discover_service`

**Files:**

- Create: `backend/app/services/discover_service.py`
- Modify: `backend/app/api/notebooks.py`（Task 4 调用，可先 stub）

- [ ] **实现函数（签名示例）**

- `async def publish_notebook(db, user_id, notebook_id, body) -> None`  
  - 校验 notebook.owner == user_id。  
  - 若 `share_token` 为空：调用与 `enable_or_rotate` 相同逻辑生成 token（可抽取 `_ensure_share_token`）。  
  - `INSERT` or merge `NotebookDiscoverProfile`。

- `async def unpublish_notebook(db, user_id, notebook_id) -> None`  
  - 删除 profile 行；**不**删 `notebook_subscriptions`（spec §6）。

- `async def list_discoverable(db, q, category, offset, limit) -> tuple[list[Row], int]`  
  - join `Notebook` + `NotebookDiscoverProfile` + `User`（owner）。  
  - `Notebook.share_token.isnot(None)` 且 profile 存在。  
  - `ilike` 搜索 title/description（MySQL 用 `collate` 或 `like` 按项目惯例）。

- `async def get_discover_detail(db, notebook_id) -> Row | None`  
  - 同上 join；用于详情。

- `async def subscribe(db, subscriber_id, notebook_id) -> None`  
  - 拒绝 `notebook.user_id == subscriber_id`。  
  - 要求 profile 存在且 `share_token` 非空。  
  - `insert` subscription；`subscriber_count += 1` 在同一事务。

- `async def unsubscribe(db, subscriber_id, notebook_id) -> None`  
  - 删除 subscription；`subscriber_count = max(0, count-1)`。

- [ ] **Commit**

```bash
git add backend/app/services/discover_service.py
git commit -m "feat(services): discover publish and subscription logic"
```

---

## Task 4: 上架路由（owner）

**Files:**

- Modify: `backend/app/api/notebooks.py`

- [ ] **增加路由**

- `POST /api/notebooks/{notebook_id}/discover/publish`，body `DiscoverPublishBody`，`Depends(get_current_user)`，调用 `publish_notebook`。
- `DELETE /api/notebooks/{notebook_id}/discover/publish`，调用 `unpublish_notebook`。

- [ ] **手动 curl 验证（需有效 JWT）**

```bash
# publish
curl -sS -X POST "http://localhost:8000/api/notebooks/<NB_ID>/discover/publish" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"category":"tech","cover_url":""}'
```

Expected: `200` 或 `204`（按你选的响应类型）；重复上架 idempotent。

- [ ] **Commit**

```bash
git add backend/app/api/notebooks.py
git commit -m "feat(api): notebook discover publish endpoints"
```

---

## Task 5: 公开发现 API

**Files:**

- Create: `backend/app/api/public_discover.py`
- Modify: `backend/app/main.py`

- [ ] **路由**

```python
# backend/app/api/public_discover.py — 核心形状
router = APIRouter(prefix="/api/public/discover", tags=["public-discover"])

@router.get("/notebooks", response_model=DiscoverNotebookListResponse)
async def list_public_discover(...): ...

@router.get("/notebooks/{notebook_id}", response_model=DiscoverNotebookDetail)
async def get_public_discover_detail(...): ...
```

- [ ] **`main.py`**

```python
from app.api import public_discover
app.include_router(public_discover.router)
```

- [ ] **Commit**

```bash
git add backend/app/api/public_discover.py backend/app/main.py
git commit -m "feat(api): public discover list and detail"
```

---

## Task 6: 订阅 API（需登录）

**Files:**

- Create: `backend/app/api/discover.py`
- Modify: `backend/app/main.py`

- [ ] **路由**

`router = APIRouter(prefix="/api/discover", tags=["discover"])`

- `POST /notebooks/{notebook_id}/subscribe` → `subscribe`
- `DELETE /notebooks/{notebook_id}/subscribe` → `unsubscribe`

均 `Depends(get_current_user)`。

- [ ] **Commit**

```bash
git add backend/app/api/discover.py backend/app/main.py
git commit -m "feat(api): discover subscribe and unsubscribe"
```

---

## Task 7: 自有「已上架」与「订阅」列表

**Files:**

- Modify: `backend/app/api/notebooks.py`（或新建 `notebook_lists.py` 并 include；为减少文件可放 notebooks.py）
- Modify: `backend/app/schemas/notebook.py`（若需在 `NotebookResponse` 增加 `discover_published: bool`）

- [ ] **`GET /api/notebooks/published`**

返回当前用户拥有且存在 `discover_profile` 的笔记本列表（复用 `_notebook_response` 与 source_count 子查询）。

- [ ] **`GET /api/notebooks/subscriptions`**

join `NotebookSubscription` + `Notebook` + `User`（owner）+ source count；每条包含：

- `notebook` 常规字段；
- `read_available: bool` = `notebook.share_token is not None`；
- `share_path`：若可读则为前端拼接 `/shared/{token}` 所需 token 或完整 path（二选一在实现定稿）。

- [ ] **Commit**

```bash
git add backend/app/api/notebooks.py backend/app/schemas/notebook.py
git commit -m "feat(api): list published and subscribed notebooks"
```

---

## Task 8: 后端 pytest

**Files:**

- Create: `backend/tests/test_discover_api.py`

- [ ] **使用 `httpx.AsyncClient` + `app` from `main`**

若项目无统一 async client fixture，参考 FastAPI 文档在测试文件内：

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_public_discover_list_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/public/discover/notebooks")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 0
    assert "items" in body
```

- [ ] **补充用例（每个独立 async test）**

1. Owner publish 后 public list `total >= 1`。  
2. 非 owner `POST publish` → `403` 或 `404`。  
3. 用户 A 订阅 B 的本 → `201`；重复订阅 `409` 或幂等 `200`（实现选定并写断言）。  
4. Owner 订阅自己 → `400`。  
5. `unpublish` 后订阅行仍在；detail `share_token` 可为 `null` 时前端逻辑由 list `read_available` 体现。

（若测试需要 DB：使用项目现有 SQLite/MySQL 测试策略；若无 DB fixture，优先 ASGITransport + dependency override 内存 SQLite——与仓库惯例一致。）

- [ ] **运行**

```bash
cd backend && uv run pytest backend/tests/test_discover_api.py -v
```

Expected: 全绿。

- [ ] **Commit**

```bash
git add backend/tests/test_discover_api.py
git commit -m "test(api): discover publish and subscribe"
```

---

## Task 9: 前端 API 层

**Files:**

- Create: `frontend/src/api/discover.ts`
- Modify: `frontend/src/api/notebook.ts`

- [ ] **`discover.ts` 使用现有 `client` 与 `publicClient.ts` 中的无鉴权 axios 实例（源码变量名 `publicOnly`）**

- `fetchDiscoverNotebooks(params)` → `publicOnly.get('/public/discover/notebooks', { params })`（`publicClient.ts` 中 `baseURL` 为 `/api`，与 `fetchPublicFeaturedNotebooks` 的 `/public/...` 写法一致）。
- `fetchDiscoverNotebookDetail(id)`。
- `subscribeDiscoverNotebook(id)`、`unsubscribeDiscoverNotebook(id)` → 需 Bearer 的 `client`。

- [ ] **`notebook.ts`**

增加 `listPublished(): Promise<{ notebooks: Notebook[] }>`、`listSubscriptions(): Promise<{ items: SubscribedNotebookItem[] }>`（`SubscribedNotebookItem` 在 `notebook.ts` 内 `export interface`）。

- [ ] **Commit**

```bash
git add frontend/src/api/discover.ts frontend/src/api/notebook.ts
git commit -m "feat(frontend): discover and subscription API clients"
```

---

## Task 10: 路由与发现页骨架

**Files:**

- Modify: `frontend/src/router/index.ts`
- Create: `frontend/src/views/DiscoverPage.vue`

- [ ] **路由**（置于 `localizedChildren`，与 `app` 同级）

```ts
{
  path: 'discover',
  name: 'Discover',
  component: () => import('@/views/DiscoverPage.vue'),
  meta: { requiresAuth: false },
},
```

- [ ] **`DiscoverPage.vue`**

- 顶栏：标题「发现」、搜索框、`v-progress-linear` 加载态。  
- 主体：精选区（可先复用 `fetchPublicFeaturedNotebooks` 与现有卡片样式简化版）、分类横向 `v-tabs`（静态 categories 数组）、`v-row`/`v-col` 双列 `DiscoverNotebookCard`。  
- 点击卡片：`router.push` 到 `/shared/:token` 若详情返回 token；否则 `Snackbar` 提示不可用。

- [ ] **Commit**

```bash
git add frontend/src/router/index.ts frontend/src/views/DiscoverPage.vue
git commit -m "feat(frontend): discover route and page shell"
```

---

## Task 11: `DiscoverNotebookCard` 组件

**Files:**

- Create: `frontend/src/components/discover/DiscoverNotebookCard.vue`

- [ ] **Props：`title`, `description`, `subscriberCount`, `sourceCount`, `ownerLabel`, `coverUrl`，emit `click`**

- [ ] **Commit**

```bash
git add frontend/src/components/discover/DiscoverNotebookCard.vue
git commit -m "feat(frontend): discover notebook card component"
```

---

## Task 12: HomePage 顶栏 + 三 Tab

**Files:**

- Modify: `frontend/src/views/HomePage.vue`
- Modify: `frontend/src/stores/useNotebookStore.ts`
- Modify: `frontend/src/locales/zh-CN.ts`、`en.ts`

- [ ] **顶栏 `header-right` 增加「发现」`v-btn`**，`@click` → `router.push({ name: 'Discover', params: { locale: ... } })`（与 `goSettings` 同模式解析 locale）。

- [ ] **在 `homeTab === 'mine'` 时，于 `home-tabs` 下方增加第二行水平 Tab**

状态：`notebookScopeTab: 'mine' | 'published' | 'subscribed'`（命名避免与 `homeTab` 混淆）。

- [ ] **数据**

- `mine`：沿用 `notebookStore.fetchNotebooks()`。  
- `published`：`notebookApi.listPublished()`。  
- `subscribed`：`notebookApi.listSubscriptions()`；卡片上若 `!read_available` 显示灰色「暂时不可用」且禁用跳转。

- [ ] **我的笔记本列表：对已存在于 `published` 集合的 id 显示小 chip「已上架」**（与 spec 一致）。

- [ ] **i18n**

键示例：`discover.title`、`discover.searchPlaceholder`、`home.notebookTabMine`、`home.notebookTabPublished`、`home.notebookTabSubscribed`、`home.discoverNav`。

- [ ] **Commit**

```bash
git add frontend/src/views/HomePage.vue frontend/src/stores/useNotebookStore.ts frontend/src/locales/zh-CN.ts frontend/src/locales/en.ts
git commit -m "feat(frontend): discover nav and notebook scope tabs"
```

---

## Task 13: 笔记本详情 / 设置 入口上架 UI（可选但推荐）

**Files:**

- Modify: `frontend/src/views/NotebookDetail.vue` 或共享 `ShareDialog` 附近

- [ ] **Owner 在「共享」流程附近增加「上架到发现」开关 + 分类/封面（最小：仅开关调用 publish/unpublish）**

- [ ] **Commit**

```bash
git add frontend/src/views/NotebookDetail.vue
git commit -m "feat(frontend): publish notebook to discover from detail"
```

---

## Task 14: 文档与 spec 状态

**Files:**

- Modify: `docs/superpowers/specs/2026-05-11-shared-notebooks-discovery-design.md`

- [ ] **将状态改为「已批准 / 已实现（MVP）」并加一行指向本 plan**

- [ ] **Commit**

```bash
git add docs/superpowers/specs/2026-05-11-shared-notebooks-discovery-design.md
git commit -m "docs: mark discover spec implemented MVP"
```

---

## Plan self-review

| Spec 章节 | 覆盖 Task |
|-----------|-----------|
| §2 水平 Tab + 文案 | Task 12 |
| §2 发现顶栏 | Task 10、12 |
| §4 数据模型 | Task 1 |
| §5 API | Task 2–7 |
| §6 下架保留订阅 | Task 3 `unpublish` + Task 7 `read_available` |
| §7 前端模块 | Task 9–13 |
| §9 测试 | Task 8 |
| §8 Admin | 明确 Phase 2，未覆盖 |

**Placeholder scan：** 无 TBD；可选路径已在 Task 7 `read_available` 说明。

**Type consistency：** `DiscoverNotebookListItem` / 前端 `DiscoverNotebookCard` props 需在 Task 9–11 对齐同一字段名。

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-11-shared-notebooks-discovery.md`.

**Two execution options:**

1. **Subagent-Driven（推荐）** — 每个 Task 新开 subagent，任务间人工快速 review。  
2. **Inline Execution** — 本会话用 executing-plans 按 Task 批量做，并在每 2–3 个 Task 后 checkpoint。

**Which approach do you want?**（若未指定，默认按 **1** 理解：你可在 Cursor 里逐 Task 指派实现。）
