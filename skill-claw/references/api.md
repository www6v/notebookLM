# NotebookLM OpenAPI

## 认证 Header

```
notebooklm-openapi-clientid: {NOTEBOOKLM_OPENAPI_CLIENTID}
notebooklm-openapi-apikey: {NOTEBOOKLM_OPENAPI_APIKEY}
Content-Type: application/json
```

## 响应格式

```json
{"code": 0, "msg": "ok", "data": {}}
```

`code != 0` 时将 `msg` 展示给用户。常见：`20004` 鉴权失败。

## API Key 管理（Web JWT，非 skill 调用）

| 方法 | 路径 | UI | 说明 |
| ---- | ---- | --- | ---- |
| GET | `/api/open-api/credential` | 图2/图3 | `has_credential=false` 空态；`true` 时返回 client_id、status_label（有效）、expires_at，**不含 api_key** |
| POST | `/api/open-api/credential` | 图2→图1 | 首次「获取 API Key」；返回 `api_key`（仅展示一次）+ client_id；已存在则 409 |
| DELETE | `/api/open-api/credential` | 图4→图2 | 删除并使 Key 失效；返回 `{has_credential:false}` |
| POST | `/api/open-api/credential/regenerate` | 图3→图1 | 「重新获取」；返回新 `api_key`（仅一次）；无 Key 时 404 |

## OpenAPI 端点（POST）

Base: `{NOTEBOOKLM_BASE_URL}/openapi/notebook/v1/`

### 笔记本

| 路径 | Body | 说明 |
| ---- | ---- | ---- |
| `list_notebooks` | `{}` | 列表 |
| `get_notebook` | `{"notebook_id":"..."}` | 详情 |
| `create_notebook` | `{"title":"...","description":""}` | 新建 |
| `update_notebook` | `{"notebook_id":"...","title":"..."}` | 更新 |
| `delete_notebook` | `{"notebook_id":"..."}` | 删除 |

### 资料来源

| 路径 | Body | 说明 |
| ---- | ---- | ---- |
| `list_sources` | `{"notebook_id":"..."}` | 列表 |
| `get_source_content` | `{"source_id":"..."}` | 正文 |
| `add_source` | `{"notebook_id":"...","type":"web","url":"https://..."}` | 添加网页 |
| `check_repeated_names` | `{"notebook_id":"...","params":[{"name":"a.pdf"}]}` | 上传前重名检查 |
| `create_media` | `{"notebook_id":"...","file_name":"a.pdf","file_size":123,"content_type":"application/pdf","file_ext":"pdf"}` | 获取 COS 上传凭证 |
| `confirm_source_upload` | `{"notebook_id":"...","source_id":"...","title":"a.pdf","file_info":{...}}` | COS 上传完成后确认 |

**文件上传流程**（与 IMA 对齐）：`check_repeated_names` → `create_media` → `cos-upload.cjs`（`--presigned-url`）→ `confirm_source_upload`。

`create_media` 返回 `cos_credential`：`presigned_put_url`、`cos_key`、`bucket_name`、`region` 等。Agent 仅将文件 PUT 到预签名 URL，不向 COS 发送 API Key。

`type` 支持（`add_source`）：`web`, `youtube`, `bilibili` 等（与 Web 端一致）。

### 笔记

| 路径 | Body | 说明 |
| ---- | ---- | ---- |
| `list_notes` | `{"notebook_id":"..."}` | 列表 |
| `get_note_content` | `{"note_id":"..."}` | 读取 |
| `create_note` | `{"notebook_id":"...","title":"...","content":"..."}` | 新建 |
| `update_note` | `{"note_id":"...","title":"...","content":"..."}` | 覆盖更新 |
| `append_note` | `{"note_id":"...","content":"..."}` | 末尾追加 |

### Skill 更新

| 路径 | Body |
| ---- | ---- |
| `check_skill_update` | `{"version":"1.0.0"}` |
