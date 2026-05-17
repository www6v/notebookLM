# Notes（笔记）

| 意图 | 接口 | 说明 |
| ---- | ---- | ---- |
| 列出笔记 | `list_notes` | 需 `notebook_id` |
| 读取 | `get_note_content` | 需 `note_id` |
| 新建 | `create_note` | `notebook_id`, `title`, `content` |
| 覆盖更新 | `update_note` | `note_id`, 可选 `title`/`content` |
| 追加 | `append_note` | `note_id`, `content`（敏感：需用户明确目标笔记） |

写入前确保 `content` 为合法 UTF-8。
