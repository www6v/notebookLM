# Sources（资料来源）

| 意图 | 接口 | 关键参数 |
| ---- | ---- | -------- |
| 列出资料 | `list_sources` | `notebook_id` |
| 读取正文 | `get_source_content` | `source_id` |
| 添加网页 | `add_source` | `notebook_id`, `type":"web"`, `url` |

```bash
node notebooklm_api.cjs "openapi/notebook/v1/add_source" \
  '{"notebook_id":"...","type":"web","url":"https://example.com","title":"示例"}'
```

文件上传需使用 Web 端；OpenAPI 当前支持 URL 类来源导入。
