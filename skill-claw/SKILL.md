---
name: notebooklm-skill
description: |
  NotebookLM OpenAPI 技能：通过 OpenClaw 检索、导入、读写笔记本（notebook）、资料来源（source）与笔记（note）。
  当用户提到笔记本、资料库、来源、笔记、导入网页、查看笔记本内容时使用此 skill。
homepage: https://github.com/notebooklm
metadata:
  openclaw:
    emoji: 📓
    requires:
      env:
        - NOTEBOOKLM_OPENAPI_CLIENTID
        - NOTEBOOKLM_OPENAPI_APIKEY
    primaryEnv: NOTEBOOKLM_OPENAPI_CLIENTID
  security:
    credentials_usage: |
      需要用户在 NotebookLM 控制台获取 Client ID 与 API Key，仅作为 HTTP Header 发送至 NotebookLM 后端。
      凭证不会写入日志或第三方域名。
    allowed_domains:
      - localhost
      - '127.0.0.1'
---

# notebooklm-skill

通过 NotebookLM OpenAPI 管理**笔记本**、**资料来源**与**笔记**。API 路径前缀：`openapi/notebook/v1`。

## 凭证配置

!`test -f ~/.config/notebooklm/client_id && test -f ~/.config/notebooklm/api_key && echo "✅ Credentials configured" || echo "⚠️ NO CREDENTIALS — setup required before any API call"`

**若未配置凭证**，引导用户：

1. 登录 NotebookLM Web，打开 **Agent 接口 / OpenClaw 配置** 页面（与 [ima agent-interface](https://ima.qq.com/agent-interface) 类似）
2. 获取 **Client ID** 与 **API Key**（可删除、重新获取）
3. 保存凭证：

```bash
mkdir -p ~/.config/notebooklm
echo "your_client_id" > ~/.config/notebooklm/client_id
echo "your_api_key" > ~/.config/notebooklm/api_key
```

或使用环境变量：

```bash
export NOTEBOOKLM_OPENAPI_CLIENTID="your_client_id"
export NOTEBOOKLM_OPENAPI_APIKEY="your_api_key"
export NOTEBOOKLM_BASE_URL="https://your-notebooklm-host"
```

## API 调用

```bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
OPTS=$(printf '{"clientId":"%s","apiKey":"%s","baseUrl":"%s"}' \
  "$NOTEBOOKLM_OPENAPI_CLIENTID" "$NOTEBOOKLM_OPENAPI_APIKEY" "${NOTEBOOKLM_BASE_URL:-http://localhost:8000}")

node "$SKILL_DIR/notebooklm_api.cjs" "openapi/notebook/v1/list_notebooks" '{}' "$OPTS"
```

- **stdout**：`{"code":0,"msg":"ok","data":{...}}`
- **stderr**（进程非 0）：`{"code":-100|-200,"msg":"..."}`

## 模块决策

| 用户意图 | 接口 |
| -------- | ---- |
| 列出/搜索笔记本 | `list_notebooks` |
| 查看单个笔记本 | `get_notebook` |
| 新建/改/删笔记本 | `create_notebook` / `update_notebook` / `delete_notebook` |
| 列出资料、读正文、添加网页来源 | `list_sources` / `get_source_content` / `add_source` |
| 列出/读/写/追加笔记 | `list_notes` / `get_note_content` / `create_note` / `update_note` / `append_note` |

详细参数见 `references/api.md`。

## 子模块

- 笔记本：`notebooks/SKILL.md`
- 资料来源：`sources/SKILL.md`
- 笔记：`notes/SKILL.md`
