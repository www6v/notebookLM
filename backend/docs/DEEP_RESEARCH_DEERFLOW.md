# Deep Research（DeerFlow 集成）

本后端通过 [bytedance/deer-flow](https://github.com/bytedance/deer-flow) 实现 **Deep Research** 功能：用户输入研究主题后，由 DeerFlow 进行网络搜索与多来源综合，生成结构化报告。

## 生产级部署要点

1. **DeerFlow 独立部署**  
   DeerFlow 需单独以服务形式运行（Docker 或 `make dev`），本后端通过 HTTP 调用其 LangGraph + Gateway API。

2. **环境变量**  
   - `DEER_FLOW_BASE_URL`：DeerFlow 统一入口（默认 `http://localhost:2026`）。  
   - 生产环境示例：`https://deerflow.your-domain.com` 或内网 `http://deer-flow:2026`。

3. **超时**  
   - `deer_flow_timeout_seconds`（默认 600）：单次研究任务 HTTP 流式请求超时，可按需调大。

4. **数据库**  
   - 执行迁移以创建 `deep_research_reports` 表：  
     `alembic upgrade head`

5. **API 流程**  
   - 前端 `POST /api/notebooks/{notebook_id}/deep-research` 创建任务（返回 202）。  
   - 轮询 `GET /api/deep-research/{report_id}` 直至 `status` 为 `ready` 或 `error`。  
   - 报告内容存于 `content`，来源数/热门数由 DeerFlow 报告末尾解析或默认 0。

## 本地/开发环境运行 DeerFlow

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
make config   # 生成 config.yaml、.env
# 编辑 config.yaml 配置模型，在 .env 中配置 API Key
make docker-start   # 或 make dev
# 访问 http://localhost:2026
```

将本后端的 `DEER_FLOW_BASE_URL` 设为 `http://localhost:2026`（或 Docker 网络内对应地址）即可联调。

## 报告内容格式

DeerFlow 返回的报告为文本/ Markdown。前端当前使用 `v-html` 展示；若需更好排版，可在前端接入 Markdown 渲染，或在后端将 Markdown 转为 HTML 后再写入 `content`。
