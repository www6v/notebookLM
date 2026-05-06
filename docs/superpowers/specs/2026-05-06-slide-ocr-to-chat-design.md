# 幻灯片预览：区域蒙版 + OCR 填入对话 — 设计说明（Spec）

## 1. 目的与范围

在 **PPT/幻灯片详情**（全屏 `SlideDeckPreviewDialog`）中，用户通过 **悬停** 高亮 OCR 识别出的文字区域（蒙版/描边），**双击** 选中区域后，将该区域的识别文本 **写入中间栏「对话」输入框**，作为待发送的用户问题。

**选型（已确认）**

- **OCR 执行位置：后端（选项 2）**  
  浏览器只负责上传当前幻灯片位图、展示区域框与交互；识别与版面聚合在服务端完成，便于统一依赖、控制体积与升级模型。

**In scope**

- 后端：接收单张幻灯片栅格图（PNG/JPEG/WebP），返回与图像像素一致的 **区域列表**（矩形 + 文本）。
- 前端：提供 **「识别」** 按钮，由用户 **手动触发** OCR；识别完成后在预览主图上叠层交互；悬停命中区域 → 视觉蒙版/描边；双击 → 将文本注入 `ChatPanel` 的输入框（与现有 `inputText` 行为一致）。
- 认证用户与 **分享只读**（`share_token`）两种场景下，均能调用 OCR（分享页无 JWT，需独立匿名安全边界，见 §6）。

**Out of scope（本阶段不做）**

- 矢量 PDF 文字层直接抽取（当前预览为 **`<img>` 位图**，与本 spec 一致）。
- 像素级「通用实例分割」（如 SAM）或独立 ML 服务；本阶段以 **RapidOCR 文本行框** 近似「组件」（每行一条区域，便于悬停选中）。
- 自动发送消息：仅 **填入输入框**，是否发送由用户决定。
- 多语言 OCR 包动态切换（首版固定 `chi_sim+eng`）。

---

## 2. 背景与现状

| 位置 | 现状 |
|------|------|
| 幻灯片详情 | `frontend/src/components/studio/SlideDeckPreviewDialog.vue`：主区为 `<img>`，URL 来自 manifest（preview/thumb，可为 blob 或 `/api` 代理）。带 `transform: scale(zoom)`。 |
| 幻灯片元数据 | `slides_data` 含标题、要点等 **无像素 bbox**，无法不经 OCR 直接画红框。 |
| 对话输入 | `frontend/src/components/chat/ChatPanel.vue`：`v-textarea` 绑定 `inputText`；与 `StudioPanel` 在 `NotebookDetail` 中为兄弟组件。 |
| 分享 | `SlideDeckPreviewDialog` 接收 `shareToken`；`shareReadApi` / `shareClient` 无 JWT。 |

---

## 3. 用户体验（UX）

1. **触发识别（手动）**：幻灯片预览 **不在** 主图加载完成后自动请求 OCR。页面上须提供固定 **「识别」** 按钮（建议放在标题栏工具区或主图一角，与「打开 PDF」等并列，具体布局实现时定稿）。**仅当用户点击「识别」** 时，前端才将 **当前页主图** 对应的 **与主图一致的图像字节** 提交后端 OCR。请求进行中按钮 **loading / disabled**，避免重复提交。未识别前：不展示可交互的文字区域蒙版（或展示禁用态提示「请先点击识别」——二选一，实现时取更轻的一种）。同一页 **再次点击「识别」** 视为重新识别（覆盖该页缓存结果）。可选优化：若已存在该 `deckId + slideIndex` 的成功结果且主图未变，可提示「已识别，再次点击将重新识别」或直接静默复用缓存（首版允许实现为 **每次点击都请求后端** 以降低复杂度）。
2. **进行中**：用户点击「识别」后，主图区域或全局轻量提示 **「正在识别版式…」**；失败时 Snackbar + 可重试（再次点击「识别」）。
3. **悬停**：鼠标位于主图内容区时，根据 **图像坐标 → 命中区域**（见 §5.2）高亮 **一个** 区域：推荐策略为「包含指针的矩形中 **面积最小** 者」，以在嵌套/重叠时偏向更细的「组件块」。
4. **蒙版视觉**：命中区域 **红色细描边**（与产品示意图一致）；可选：非命中区域 **轻微压暗**（`rgba` 遮罩），注意对比度与无障碍。
5. **双击**：若当前有命中区域且 `text.trim()` 非空，则 **注入对话输入框**（策略见 §5.3）；若无文字或只读模式，见 §5.4。
6. **缩放**：缩放后命中检测仍与 **屏幕上的图像几何** 一致（使用 `getBoundingClientRect` 与 `naturalWidth/Height` 映射）。

---

## 4. 后端设计

### 4.1 依赖与运行环境

- **Python**：[RapidOCR](https://rapidai.github.io/RapidOCRDocs/latest/install_usage/rapidocr/install/)（`rapidocr` + **`onnxruntime`** CPU 推理；默认 PP-OCRv4 中英文模型，随包或首次运行时拉取）。
- **镜像**：无需 `tesseract-ocr`；建议保留 `libglib2.0-0`、`libgomp1` 等以兼容 `opencv-python` / ONNX Runtime 在 slim 下的运行（见当前 `backend/Dockerfile`）。
- **失败**：若 `rapidocr` / `onnxruntime` 未安装或初始化失败，接口返回 **503**，`detail` 说明原因（便于运维排查）。

### 4.2 处理管线

1. 校验 `Content-Type` ∈ `{ image/png, image/jpeg, image/webp }`。
2. 限制请求体大小（建议 **≤ 12MB**，与 nginx `client_max_body_size` 对齐或略小）。
3. `Pillow` 打开图像 → RGB；按实现可做 **适度缩放/增强** 后送 RapidOCR；将检测框坐标 **映射回** **原图像素**，与前端展示一致。
4. RapidOCR **检测 + 方向分类 + 识别**；每条文本行对应 **一个矩形区域**（由四边形框取轴对齐外接矩形）及 `text`。
5. 过滤低置信度行与极小噪点框（最小面积、最小边长、分数阈值等常量）。
6. 返回 JSON：

```json
{
  "width": 1920,
  "height": 1080,
  "regions": [
    { "x": 120, "y": 340, "w": 280, "h": 96, "text": "Spider 2.0: 企业级…" }
  ]
}
```

- `width` / `height`：**原图**尺寸（与 `regions` 坐标系一致）。

### 4.3 API 形态

| 路由 | 鉴权 | 说明 |
|------|------|------|
| `POST /api/ocr/slide-image-layout` | `get_current_user` | `multipart/form-data`，字段名建议 `file`。 |
| `POST /api/share/{share_token}/ocr/slide-image-layout` | 校验 `share_token` 对应笔记本存在且分享开启 | 与现有 `share_read` 前缀一致；**不**携带 JWT。 |

两条路由 **共享同一服务函数**（避免逻辑分叉）。分享路由仅证明「匿名访客持有有效 share token」，不要求其拥有笔记本写权限。

### 4.4 错误与状态码

| 场景 | HTTP |
|------|------|
| 格式不支持 / 空文件 | 400 |
| 超过大小限制 | 413 |
| RapidOCR / ONNX 未就绪或推理失败 | 503 |
| 分享 token 无效 | 404（与现有 share 行为一致） |

---

## 5. 前端设计

### 5.1 组件改动面

| 文件 | 职责 |
|------|------|
| `SlideDeckPreviewDialog.vue` | 增加 **「识别」** 按钮；主图外包一层 `position: relative` 容器；叠 **透明交互层**（与图同显式尺寸）；**点击「识别」后** 请求 OCR、绘制高亮、处理 `mousemove` / `dblclick`。 |
| `StudioPanel.vue` | 向 `SlideDeckPreviewDialog` 传入 `read-only`（与现有 `readOnly` 一致），供注入策略判断。 |
| 新建 `frontend/src/api/ocrLayout.ts` | 封装 `FormData` POST 至 `/api/ocr/slide-image-layout`。 |
| `frontend/src/api/shareRead.ts` | 增加分享版 OCR POST（`shareClient` + 正确 `baseURL` 路径）。 |
| `useChatStore.ts` | 增加「待注入对话草稿」机制（见下），避免兄弟组件硬编码事件总线。 |
| `ChatPanel.vue` | `watch` 草稿序号或 payload，合并到 `inputText`，`nextTick` 聚焦输入区。 |
| `zh-CN.ts` / `en` 等 | Snackbar 与提示文案（按钮文案「识别」、OCR 中、失败、只读无法注入等）。 |

### 5.2 坐标映射

设图像元素 `naturalWidth = W`，`naturalHeight = H`，`getBoundingClientRect()` 宽 `Rw`、高 `Rh`（已含 CSS 缩放）。指针相对图像左上角：

- `nx = (clientX - left) / Rw * W`
- `ny = (clientY - top) / Rh * H`

在 `(nx, ny)` 上做矩形包含判定；多命中时取 **面积最小** 区域。

### 5.3 注入对话策略

- **默认**：`inputText = region.text.trim()`（**替换**当前草稿，符合「从幻灯片摘一句去问」）。
- **可选后续**：Shift+双击为追加（本 spec 不强制首版实现）。

### 5.4 只读（分享）模式

- `ChatPanel` 在 `readOnly` 下 **不展示输入框** 时：双击仍可做 OCR 高亮，但 **不调用**注入；Snackbar 提示「分享视图无法填入对话」类文案（避免静默失败）。

### 5.5 请求与性能

- OCR 请求超时建议 **120s**（单独配置，勿用默认 30s）。
- **不在** 切换 `selectedIndex` 或主图 URL 时自动请求；仅响应 **「识别」** 点击。
- 切换幻灯片页码时：清空当前页交互层状态，直至用户对新页再次点击「识别」（若实现本地缓存，可按 `deckId + slideIndex` 复用已识别结果并跳过请求，见 §3 第 1 点可选说明）。
- 内存：关闭弹窗时清空缓存与区域数据。

---

## 6. 安全与滥用控制

- **认证路由**：仅登录用户。
- **分享路由**：必须 `_notebook_for_share` 校验；不泄露其他笔记本数据；与读幻灯片图同一信任级别。
- **速率**：首版可依赖全局网关/反代；若滥用明显，后续对 `share_token` + IP 做限流（本 spec 记为 follow-up）。
- **隐私**：图像经 OCR 在服务端内存处理，**不落盘**（除非后续审计需求变更）。

---

## 7. 验收标准（Acceptance）

1. 登录用户在笔记本中打开幻灯片预览，**点击「识别」并完成 OCR 后**，悬停在某段文字区域可见 **稳定高亮框**（与识别区域一致 order of magnitude）；未点击「识别」前 **不会** 向后端发起 OCR 请求。
2. 双击该区域后，中间栏对话 **输入框**出现对应文字（trim 后），光标可聚焦。
3. 缩放 0.5x～3x 时，悬停与双击仍命中正确区域（允许 ± 几个像素误差）。
4. 后端 OCR 依赖未就绪时，前端收到 503，有 **明确错误提示**。
5. 有效 `share_token` 下可完成 OCR；`readOnly` 且无输入框时不注入并有提示。

---

## 8. 依赖与运维清单

- [ ] 生产/测试镜像安装 `rapidocr`、`onnxruntime`（及 Dockerfile 中 OCR 所需系统库）。
- [ ] 离线环境需预置 RapidOCR ONNX 模型或允许容器访问模型下载地址。
- [ ] `main.py` 注册 `ocr_layout` 路由；`share_read.py` 注册分享 OCR 子路由。
- [ ] 若有 nginx，`client_max_body_size` ≥ OCR 上传上限。

---

## 9. 后续可增强（非本 spec 承诺）

- 后端聚类算法升级（行聚块、DBSCAN）以改善复杂排版。
- 前端缓存 ETag / 图片 hash 减少重复 OCR。
- 与 DashScope 等云端 OCR 可配置切换（多租户计费）。

---

## 10. 与已实现代码的对照（可选追踪）

仓库中若已存在 `backend/app/api/ocr_layout.py`、`backend/app/services/ocr/slide_layout_ocr.py` 等文件，应 **以本 spec 为需求源** 做 diff 审查；若尚未合并路由与 Docker 依赖，按 §8 补齐后再联调前端。

**文档版本**：2026-05-06  
**状态**：**已确认** — 可作为实现与验收依据；下一步为按 §5–§8 编码与联调（implementation）。
