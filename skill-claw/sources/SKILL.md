# Sources（资料来源）

API 前缀：`openapi/notebook/v1`

## 接口决策表

| 用户意图 | 调用接口 | 关键参数 |
| -------- | -------- | -------- |
| 上传文件到笔记本 | `check_repeated_names` → `create_media` → COS Upload → `confirm_source_upload` | `notebook_id`，`file_name`，`file_size` |
| 添加网页/视频链接 | `add_source` | `notebook_id`，`type`，`url` |
| 列出资料 | `list_sources` | `notebook_id` |
| 读取正文 | `get_source_content` | `source_id` |
| 检查文件名是否重复 | `check_repeated_names` | `params[].name`，`notebook_id` |

---

## ⛔ 文件上传安全门

```
GATE 1 [TYPE CHECK]
  先运行 preflight-check.cjs。pass=false → 立即拒绝，不要问「是否仍要尝试」。

GATE 2 [NAMING]
  confirm_source_upload 的 title 必须等于 file_name（含扩展名）。

GATE 3 [DUPLICATES]
  所有文件上传前必须调用 check_repeated_names。
  is_repeated=true → 询问用户：保留两者（文件名加 _YYYYMMDDHHmmss）或取消。

GATE 4 [UPLOAD EXIT]
  cos-upload.cjs 非 0 退出 → 立即停止，不要调用 confirm_source_upload。
```

---

## 上传文件到笔记本（完整流程）

```bash
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
SCRIPTS="$SKILL_DIR/sources/scripts"

# ── Step 1: preflight-check.cjs ← GATE 1 ──
PREFLIGHT=$(node "$SCRIPTS/preflight-check.cjs" --file "/path/to/report.pdf")
# pass=false → 终止

FILE_NAME=$(echo "$PREFLIGHT" | node -e "const d=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(d.file_name)")
FILE_EXT=$(echo "$PREFLIGHT" | node -e "const d=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(d.file_ext)")
FILE_SIZE=$(echo "$PREFLIGHT" | node -e "const d=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(String(d.file_size))")
CONTENT_TYPE=$(echo "$PREFLIGHT" | node -e "const d=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(d.content_type)")

# ── Step 2: check_repeated_names ← GATE 3 ──
node "$SKILL_DIR/notebooklm_api.cjs" "openapi/notebook/v1/check_repeated_names" \
  "{\"notebook_id\":\"<notebook_id>\",\"params\":[{\"name\":\"$FILE_NAME\"}]}" "$OPTS"

# ── Step 3: create_media ──
CREATE_RESP=$(node "$SKILL_DIR/notebooklm_api.cjs" "openapi/notebook/v1/create_media" "{
  \"notebook_id\": \"<notebook_id>\",
  \"file_name\": \"$FILE_NAME\",
  \"file_size\": $FILE_SIZE,
  \"content_type\": \"$CONTENT_TYPE\",
  \"file_ext\": \"$FILE_EXT\"
}" "$OPTS")
# 提取 source_id / media_id、cos_credential（含 presigned_put_url）

# ── Step 4: cos-upload.cjs ← GATE 4 ──
# NotebookLM 使用服务端签发的 presigned PUT（不暴露 COS 主密钥）
node "$SCRIPTS/cos-upload.cjs" \
  --file "/path/to/report.pdf" \
  --presigned-url "<cos_credential.presigned_put_url>" \
  --content-type "$CONTENT_TYPE" \
  --timeout 300000

# ── Step 5: confirm_source_upload ← GATE 2 ──
node "$SKILL_DIR/notebooklm_api.cjs" "openapi/notebook/v1/confirm_source_upload" "{
  \"notebook_id\": \"<notebook_id>\",
  \"source_id\": \"<source_id>\",
  \"title\": \"$FILE_NAME\",
  \"file_info\": {
    \"cos_key\": \"<cos_credential.cos_key>\",
    \"file_size\": $FILE_SIZE,
    \"file_name\": \"$FILE_NAME\"
  }
}" "$OPTS"
```

- COS 域名来自 `cos_credential` / 预签名 URL（`*.myqcloud.com`），**不要**把 Client ID / API Key 发往 COS。
- 大文件请增大 `--timeout`（默认 300000 ms）。

---

## 添加网页来源

```bash
node notebooklm_api.cjs "openapi/notebook/v1/add_source" \
  '{"notebook_id":"...","type":"web","url":"https://example.com","title":"示例"}'
```

`type` 支持：`web`, `youtube`, `bilibili` 等（与 Web 端一致）。
