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

## 运行环境与耗时观测

网关进程启动时会打一条 **`gateway_runtime_env`** 日志，汇总与 MinerU 相关的环境变量（设备、后端、公式/表格开关、分页等）以及 **`in_docker`**（是否检测到 `/.dockerenv`）。每次解析请求会起一个子进程执行官方 **`mineru`** CLI（与 `legal_agent` 等项目用法一致：`mineru -p … -o … -b …`）；模型加载与推理发生在该子进程内。每次 `POST /v1/parse` 还会记录 **`parse_input`**：`input_fetch_s`（JSON 模式为下载 URL 耗时，multipart 为读表单项耗时）、`pdf_bytes`、`pdf_pages`（若能用 `pypdf` / `PyPDF2` 解析页数，否则为 `None`）。主进程中的 **`MinerU CLI parse wall time`** 为整段子进程墙钟时间。若在 **macOS** 上设备为 **cpu** 且该墙钟超过 **`MINERU_GATEWAY_SLOW_HINT_SEC`**（默认 `120`），会额外打一条 **`performance_hint`**，提示尝试 MPS 或远端 GPU（见「典型慢日志与一键调优」）。

**确认环境 checklist**：本机脚本 [`scripts/run_mineru_gateway_local.sh`](../scripts/run_mineru_gateway_local.sh) 在 macOS 上未显式设置设备时默认 **`MINERU_GATEWAY_DEVICE=cpu`**；Docker 默认 CPU 版 PyTorch，见下文「GPU / CPU 镜像」。对照 `gateway_runtime_env` 与 MinerU 日志即可确认是否误跑 CPU、是否在容器内。

## 性能调优（A/B 测耗时）

在可接受的质量前提下，可通过环境变量缩短 pipeline 时间（由 [`app/main.py`](app/main.py) 映射到 `mineru` CLI 参数）：

| 变量 | 默认 | 说明 |
|------|------|------|
| `MINERU_GATEWAY_PARSE_METHOD` | `txt` | 对应 `mineru -m`：`txt` 纯文本直抽；扫描件可设 `ocr`；自动判别设 `auto` |
| `MINERU_GATEWAY_FORMULA_ENABLE` | `true` | 设为 `0`/`false`/`no`/`off` 可关闭公式识别 |
| `MINERU_GATEWAY_TABLE_ENABLE` | `true` | 同上关闭表格结构识别 |
| `MINERU_GATEWAY_START_PAGE` | `0` | 起始页（0-based） |
| `MINERU_GATEWAY_END_PAGE` | 空 | 结束页（含）；空表示直到末页 |

建议固定同一 PDF，只改一项，对比日志中的 **`MinerU CLI parse wall time`**。

### 典型慢日志与一键调优（运维）

若日志里 **`gateway_runtime_env`** 含 **`MINERU_GATEWAY_DEVICE=cpu`**，且 **`parse_input`** 页数不多但 **`MinerU CLI parse wall time`** 仍达数百秒，瓶颈通常是 **CPU 跑全量 pipeline**，而非下载。

**Apple Silicon 本机（先试 Metal）**（启动网关前执行）：

```bash
export MINERU_GATEWAY_DEVICE=mps
./scripts/run_mineru_gateway_local.sh
```

若出现 MPS OOM，见上文「Apple Silicon（本机 venv）与 MPS 显存报错」；可退回 CPU 或调小任务。

**可接受降质时加快 A/B**：

```bash
export MINERU_GATEWAY_FORMULA_ENABLE=0
export MINERU_GATEWAY_TABLE_ENABLE=0
```

**Linux + NVIDIA**：勿用默认 CPU 镜像；按「GPU / CPU 镜像」改用 CUDA 版 PyTorch，并设置 **`MINERU_DEVICE_MODE=cuda`**（或 **`MINERU_GATEWAY_DEVICE=cuda`**，与 MinerU 版本一致即可）。

**远端 GPU**：将解析迁到带 GPU 的机器或 MinerU **client + 常驻服务**（见「进程模型」），NotebookLM 仍通过同一 `mineru_base_url` 调网关或直连服务（视部署而定）。

## 进程模型：子进程 vs 常驻推理

- **默认**：每个请求起一个子进程执行官方 **`mineru`** CLI（`-p` / `-o` / `-b` 及网关环境变量映射的 `-m`、`-l`、`-f`、`-t`、分页、`-u`、`--source` 等；见 `mineru --help`）。`MINERU_CLI_EXTRA_ARGS` 以 shell 词法追加；`pipeline` 后端下若设置了 **`MINERU_GATEWAY_DEVICE`** 或 **`MINERU_DEVICE_MODE`**，会在 **参数列表末尾** 再追加 **`-d`**（可覆盖 compose 里 `MINERU_CLI_EXTRA_ARGS` 中较早出现的 `-d`）。注意 stock CLI 遇错仍可能 exit 0，网关会结合输出目录是否产生 markdown 再判失败。
- **Client 后端**：当 `MINERU_GATEWAY_BACKEND` 以 **`-client`** 结尾时，按 MinerU 文档配置 **`MINERU_GATEWAY_SERVER_URL`** 指向常驻推理服务，由远端持有模型与显存，网关只做轻量调用；具体后端名称与部署方式以官方 MinerU 版本为准。

## GPU / CPU 镜像

`Dockerfile` 在完整安装依赖后，会 **强制重装** PyTorch 的 **Linux CPU** 轮（`download.pytorch.org/whl/cpu`），避免默认 PyPI 拉取 CUDA 大包且便于无 GPU 环境。

`docker-compose.yml` 默认设置 `MINERU_DEVICE_MODE=cpu`，并在 `MINERU_CLI_EXTRA_ARGS` 未配置时传入 `-d cpu`（`mineru` 的 pipeline 设备）。若机器有 GPU 且要用 CUDA，请在 compose 或环境中覆盖上述变量，并改用 CUDA 版 torch 安装方式。

环境变量 `MINERU_CLI_EXTRA_ARGS` 可传入额外 CLI 参数（空格分隔），例如语言或后端选项（以本机 `mineru --help` 为准）。

### Apple Silicon（本机 venv）与 MPS 显存报错

若日志出现 ``MPS backend out of memory``，说明 PyTorch 在用 Metal 加速时触发了统一内存上限。`./scripts/run_mineru_gateway_local.sh` 在 **未** 设置 `MINERU_GATEWAY_DEVICE` / `MINERU_DEVICE_MODE` 的 macOS 上已默认 `MINERU_GATEWAY_DEVICE=cpu`（更稳、更慢）。

若要仍尝试 GPU 式加速，可显式 `export MINERU_GATEWAY_DEVICE=mps`；若仍 OOM，可查阅 PyTorch 文档调整 `PYTORCH_MPS_HIGH_WATERMARK_RATIO`（调高有拖垮系统的风险）。
