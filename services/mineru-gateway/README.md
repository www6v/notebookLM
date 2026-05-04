# MinerU 独立网关（NotebookLM 兼容）

与主项目 [`mineru_client`](../../backend/app/services/infra/mineru_client.py) 约定一致：

- `POST /v1/parse`，`Content-Type: application/json`：`{"pdf_url": "<预签名URL>", "output_preference": "markdown"}`
- 或 `multipart/form-data`，字段名 `pdf`（对应后端 `mineru_use_multipart: true`）
- 可选鉴权：请求头 `Authorization: Bearer <MINERU_GATEWAY_API_KEY>`
- 响应：`{"markdown": "...", "files": [{"path": "相对路径", "content_base64": "..."}]}`

本目录通过 **调用官方 `mineru` CLI** 完成解析。`requirements.txt` 使用 **`mineru[pipeline]`**（含 torch 等），否则默认后端 `hybrid-auto-engine` 会报缺少本地 pipeline 依赖。镜像体积与首次安装/构建时间会较大，属正常。

若出现 ``AttributeError: module 'torch' has no attribute 'Tensor'``，说明本机 venv 里 **torch 安装不完整**（例如磁盘满、安装中断）。在 `services/mineru-gateway` 下执行  
`pip install --force-reinstall --no-cache-dir -r requirements.txt`  
或删掉 `.venv` 后重新跑 `./scripts/run_mineru_gateway_local.sh`。

### 模型下载失败（`LocalEntryNotFoundError` / Hugging Face Hub）

MinerU pipeline 会从远端拉取权重。若默认走 **Hugging Face** 且网络访问不了 Hub，会报错。处理方式（任选其一）：

1. **推荐**：使用 **ModelScope**（本地脚本与 Docker 镜像已默认 `MINERU_MODEL_SOURCE=modelscope`）。若你自行 `uvicorn` 启动，请先执行 `export MINERU_MODEL_SOURCE=modelscope`。
2. 仍走 HF 时可用镜像：``export HF_ENDPOINT=https://hf-mirror.com``（以你环境可用的镜像为准）。
3. 完全离线：在 `~/mineru.json`（或环境变量 `MINERU_TOOLS_CONFIG_JSON` 指向的配置）中配置 MinerU 文档所述的 `models-dir` / `MINERU_MODEL_SOURCE=local`。

若坚持用 Hugging Face：``export MINERU_MODEL_SOURCE=huggingface`` 后再启动网关。

## 快速启动（Docker）

在仓库根目录执行：

```bash
./scripts/deploy_mineru.sh
```

或手动：

```bash
cd services/mineru-gateway
docker compose build
docker compose up -d
curl -s http://127.0.0.1:8765/health
```

## 与 NotebookLM 对接

在 `config.yaml` 的 `mineru` 段设置（与 [`config.yaml.example`](../../config.yaml.example) 一致）：

```yaml
mineru:
  mineru_base_url: http://127.0.0.1:8765
  mineru_api_key: your-shared-secret   # 若网关设置了 MINERU_GATEWAY_API_KEY
  mineru_parse_path: /v1/parse
  mineru_timeout_seconds: 600
  mineru_oss_presign_seconds: 7200
  mineru_use_multipart: false
```

**注意**：网关必须能访问 `pdf_url`（公网或 VPC 内 OSS 预签名链接）。

## GPU / CPU 镜像

`Dockerfile` 在完整安装依赖后，会 **强制重装** PyTorch 的 **Linux CPU** 轮（`download.pytorch.org/whl/cpu`），避免默认 PyPI 拉取 CUDA 大包且便于无 GPU 环境。

`docker-compose.yml` 默认设置 `MINERU_DEVICE_MODE=cpu`，并在 `MINERU_CLI_EXTRA_ARGS` 未配置时传入 `-d cpu`（`mineru` 的 pipeline 设备）。若机器有 GPU 且要用 CUDA，请在 compose 或环境中覆盖上述变量，并改用 CUDA 版 torch 安装方式。

环境变量 `MINERU_CLI_EXTRA_ARGS` 可传入额外 CLI 参数（空格分隔），例如语言或后端选项（以本机 `mineru --help` 为准）。

### Apple Silicon（本机 venv）与 MPS 显存报错

若日志出现 ``MPS backend out of memory``，说明 PyTorch 在用 Metal 加速时触发了统一内存上限。`./scripts/run_mineru_gateway_local.sh` 在 **未** 设置 `MINERU_GATEWAY_DEVICE` / `MINERU_DEVICE_MODE` 的 macOS 上已默认 `MINERU_GATEWAY_DEVICE=cpu`（更稳、更慢）。

若要仍尝试 GPU 式加速，可显式 `export MINERU_GATEWAY_DEVICE=mps`；若仍 OOM，可查阅 PyTorch 文档调整 `PYTORCH_MPS_HIGH_WATERMARK_RATIO`（调高有拖垮系统的风险）。
