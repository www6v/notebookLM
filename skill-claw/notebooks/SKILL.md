# Notebooks（笔记本）

API 前缀：`openapi/notebook/v1`

| 意图 | 接口 | 示例 body |
| ---- | ---- | --------- |
| 列出笔记本 | `list_notebooks` | `{}` |
| 查看详情 | `get_notebook` | `{"notebook_id":"uuid"}` |
| 新建 | `create_notebook` | `{"title":"研究项目"}` |
| 重命名/改描述 | `update_notebook` | `{"notebook_id":"uuid","title":"新标题"}` |
| 删除 | `delete_notebook` | `{"notebook_id":"uuid"}` |

```bash
node notebooklm_api.cjs "openapi/notebook/v1/list_notebooks" '{}'
```
