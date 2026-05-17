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

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/open-api/credential` | 查看 Client ID、状态、有效期 |
| POST | `/api/open-api/credential` | 首次生成（返回 api_key 一次） |
| DELETE | `/api/open-api/credential` | 删除 API Key |
| POST | `/api/open-api/credential/regenerate` | 重新获取 |

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

`type` 支持：`web`, `youtube`, `bilibili` 等（与 Web 端一致）。

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
