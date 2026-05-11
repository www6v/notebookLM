# 共享笔记本、发现与订阅 — 产品设计

**日期：** 2026-05-11  
**状态：** 待审阅（实现前需书面确认）  
**范围：** 主应用 `frontend/` + `backend/` + `shared/notebooklm_shared/`

---

## 1. 背景与目标

用户在知识库产品中需要**社交化 / 社区化**能力：未对社区公开的为个人笔记本；对全站可发现、可被他人订阅的为**共享笔记本**；用户订阅后出现在**订阅笔记本**列表。发现页支持搜索与分类浏览。

**与现状的关系**

- 已有 `Notebook.share_token`：匿名只读链接；`share_enabled` 由 API 派生。
- 已有运营精选表 `featured_notebook_links` 与公开接口 `/public/featured-notebooks`：首页「精选」Tab。
- 本设计在**不推翻**上述能力的前提下，增加「上架到发现」「订阅关系」「发现页」与侧栏三 Tab 体验。

**成功标准（MVP）**

- 侧栏：**我的笔记本** | **共享笔记本** | **订阅笔记本** 为**水平 Tab**；列表随 Tab 切换。
- 顶栏提供全局入口 **发现**（线框伴侣中已选 **A：顶栏**）。
- Owner 可将自有笔记本**上架**到发现；访客可搜索/浏览元数据；登录用户可**订阅/退订**。
- 订阅者对他人笔记本为**只读**，与现有 share 读模式一致；不在 MVP 引入订阅者编辑。

---

## 2. 信息架构与文案（已定）

| 概念 | UI 文案 | 语义 |
|------|-----------|------|
| 个人侧自有本 | **我的笔记本** | 当前用户 `user_id` 拥有的全部笔记本（含未上架与已上架）。已上架建议用**标签/角标**区分，避免用户找不到「已共享」的本。 |
| 自己对社区公开 | **共享笔记本** | 当前用户拥有且**已上架到发现**的笔记本子集。 |
| 他人公开本 | **订阅笔记本** | 当前用户已建立**订阅关系**的他人笔记本列表；卡片可带头图（与参考图一致）。 |
| 目录页 | **发现** | 顶栏入口；搜索占位 **「搜索共享笔记本」**；精选、横向分类、双列卡片（元数据见下）。 |

**发现页元数据（可分期）**

- 标题、摘要、订阅人数、内容数（可与 `source_count` 对齐）、`@作者` 展示名、可选认证标。
- 「换一换」精选：MVP 可与运营精选合并为简单随机/排序；后续再接推荐服务。

---

## 3. 实现取向与推荐

| 方案 | 说明 | MVP 适用性 |
|------|------|------------|
| **A. 扩展 Notebook + 订阅表（推荐）** | 上架字段或旁表 + `notebook_subscriptions(user_id, notebook_id)`；发现列表查询「可发现」笔记本。 | **采用**。改动面可控，与现有模型一致。 |
| B. 独立发布快照实体 | `PublishedNotebook` 版本化公开内容。 | 能力强；MVP 过重，仅作后续扩展点。 |
| C. 仅扩展运营精选 | 不做用户订阅与全站目录。 | 不满足本需求。 |

**扩展点（非 MVP）**：若未来需要「订阅快照不随 owner 大改而变」，在方案 A 上增加 `published_revision_id` 或快照表，无需推翻订阅表。

---

## 4. 数据模型（MVP）

**4.1 笔记本侧（二选一实现细节，实现阶段定稿其一）**

- **选项 1（列在 `notebooks`）**：`is_discoverable`、`discover_category`、`discover_cover_url`、`subscriber_count`（反规范化，异步维护）、`discover_published_at` 等；上架时要求 `share_token` 非空（或上架接口自动生成 token）。
- **选项 2（旁表 `notebook_discover_profiles`）**：`notebook_id` PK/FK，上述元数据放旁表，`notebooks` 保持较瘦。

推荐 **选项 2** 若希望 ORM 边界清晰；**选项 1** 若追求查询简单。Spec 不强制，实现计划里选一种并全仓一致。

**4.2 订阅**

- 表 `notebook_subscriptions`：`id`、`subscriber_user_id`、`notebook_id`、`created_at`；`UNIQUE(subscriber_user_id, notebook_id)`。
- Owner 不可订阅自己的笔记本（API 拒绝）。

**4.3 与 `featured_notebook_links`**

- 保留；发现页「精选」区块可同时展示运营配置项 + 可选算法位；排序与去重在服务层完成。

---

## 5. API 轮廓（REST，路径示例）

以下均需认证 unless 标注「可匿名」。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notebooks/{id}/discover/publish` | Owner 上架；body 含分类、封面等；校验 share 策略。 |
| DELETE | `/api/notebooks/{id}/discover/publish` | Owner 下架；订阅关系策略见 §6。 |
| GET | `/api/discover/notebooks` | **可匿名**（或仅元数据匿名）；`q`、`category`、分页。 |
| GET | `/api/discover/notebooks/{id}` | 公开详情（不含敏感 owner 信息字段由 DTO 控制）。 |
| POST | `/api/discover/notebooks/{id}/subscribe` | 登录用户订阅。 |
| DELETE | `/api/discover/notebooks/{id}/subscribe` | 退订。 |
| GET | `/api/notebooks` | 扩展或新增 query：`scope=mine|published|subscribed` **或** 保留现有 list 为 mine-only，另加 `/api/notebooks/published`、`/api/notebooks/subscriptions`（实现计划二选一，避免前端混乱）。 |

**计数**：`subscriber_count` 在订阅/退订事务或队列中维护；`content_count` 可用现有 source 计数或物化字段。

---

## 6. 权限与生命周期

- **读**：订阅者与匿名 share 读者共用只读管线（Studio/Source 等已有 share token 路径）；登录订阅可增加「带用户身份的只读」路径以减少 token 泄漏面（实现计划择优）。
- **Owner 下架或撤销 share_token**（MVP 固定）：**订阅关系保留**；在「订阅笔记本」列表中该项显示「暂时不可用」、禁用进入详情；重新上架并恢复有效只读通道后自动可点。
- **删除笔记本**：级联删除订阅行与发现 profile。

---

## 7. 前端模块

- **顶栏**：新增「发现」路由入口（与设置等并列）。
- **侧栏**：Notebook 列表区顶部 **水平 Tab**；三套数据源对应 §5 列表接口。
- **发现页**：`DiscoverPage`（或等价命名）：搜索、精选、分类 Tab、双列 `DiscoverNotebookCard`；点击进入只读预览后「订阅」主按钮。
- **状态**：扩展 `useNotebookStore` 或新增 `useDiscoverStore`；i18n 中英与「笔记本」口径一致。

---

## 8. 管理端与合规（MVP 占位）

- Admin 可增加「强制下架」与可选举报队列；**非 MVP 阻塞项** 时在实现计划中列为 Phase 2。

---

## 9. 测试与验收

- 单元/集成：上架/下架、订阅/退订、权限边界（非 owner 上架、自订阅拒绝）。
- 契约：发现列表分页与筛选。
- 可选 E2E：发现 → 订阅 → 侧栏「订阅笔记本」可见。

---

## 10. 非目标（MVP 明确不做）

- 订阅者对他人笔记本的写权限、协作文档。
- 复杂推荐算法、IM、评论区（可作为后续「社区」迭代）。

---

## 11. 假设汇总（若与产品冲突请书面修订）

1. **发现入口**：顶栏全局（线框选择 A）。  
2. **我的笔记本**：列出**全部**自有本；已上架用 UI 标签区分。  
3. **共享笔记本** Tab：仅已上架的自有本。  
4. **订阅者**：只读，与 share 体验对齐。  
5. **下架与订阅**：采用 §6 中单一路径，实现前在 spec 修订一行即可。

---

## 12. 后续流程

1. 审阅本文件；修改意见直接改 Markdown 或批注。  
2. 批准后由实现阶段使用 **writing-plans** 生成 `docs/superpowers/plans/…` 拆解任务。  
3. 本 spec **不**包含具体 Vue 组件文件名与迁移脚本细节，由实现计划补全。
