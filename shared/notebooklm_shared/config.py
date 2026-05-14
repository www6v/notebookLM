"""Application configuration loaded from config.yaml.

The repository ``.env`` (if present) is loaded into ``os.environ`` only so that
``config.yaml`` string values can use ``$VAR`` / ``${VAR}`` substitution. It is
not read as a pydantic-settings source; configure the app in ``config.yaml``.
Process environment variables still override values when set (e.g. Docker),
except Tencent COS: those values are taken only from the ``cos`` block in
``config.yaml`` (after ``$VAR`` expansion); ``COS_*`` in the process environment
are not applied as settings overrides.
"""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, InitSettingsSource, SettingsConfigDict


def _repo_root() -> Path:
    """Directory for config.yaml and optional .env.

    When called from notebooklm_shared (shared/notebooklm_shared/config.py):
    - here = .../notebookLM/shared/notebooklm_shared/config.py
    - monorepo_candidate = .../notebookLM/
    - Check: notebookLM/backend/app exists → returns notebookLM/ ✓

    In Docker (admin/backend), set NOTEBOOKLM_CONFIG_PATH=/app/config.yaml
    to bypass this discovery logic.

    When the package is installed as a wheel, ``_repo_root()`` may resolve to
    site-packages (no ``config.yaml``). In that case ``_config_yaml_path()``
    falls back to ``Path.cwd() / "config.yaml"`` so a file mounted at the
    process working directory (e.g. ``WORKDIR /app`` in the backend image) is
    picked up without extra env.
    """
    here = Path(__file__).resolve()
    backend_app = here.parent        # notebooklm_shared/
    backend_root = backend_app.parent  # shared/
    monorepo_candidate = backend_root.parent  # notebookLM/
    if (monorepo_candidate / "backend" / "app").is_dir():
        return monorepo_candidate
    return backend_root


def _ensure_dotenv_loaded() -> None:
    """Load repo ``.env`` into ``os.environ`` for ``$VAR`` expansion in YAML only."""
    path = _repo_root() / ".env"
    if path.is_file():
        load_dotenv(path, override=False)


def _config_yaml_path() -> Path:
    """Resolve config.yaml (Deer Flow–style NOTEBOOKLM_CONFIG_PATH override)."""
    override = os.environ.get("NOTEBOOKLM_CONFIG_PATH", "").strip()
    if override:
        resolved = Path(override).expanduser()
        if not resolved.is_absolute():
            resolved = Path.cwd() / resolved
        return resolved
    # Installed wheel: ``_repo_root()`` may be site-packages (no config.yaml).
    # Docker images use WORKDIR /app and mount ``./config.yaml:/app/config.yaml``.
    repo_yaml = _repo_root() / "config.yaml"
    if repo_yaml.is_file():
        return repo_yaml
    cwd_yaml = Path.cwd() / "config.yaml"
    if cwd_yaml.is_file():
        return cwd_yaml
    return repo_yaml


_ENV_VAR_REF = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)"
)


def _expand_env_in_str(value: str) -> str:
    """Replace $VAR / ${VAR} with os.environ values (Deer Flow convention)."""

    def _repl(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return os.environ.get(name, "")

    return _ENV_VAR_REF.sub(_repl, value)


def _expand_env_recursive(obj: Any) -> Any:
    """Expand environment references in all string leaves."""
    if isinstance(obj, str):
        return _expand_env_in_str(obj)
    if isinstance(obj, dict):
        return {k: _expand_env_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_recursive(v) for v in obj]
    return obj


_NESTED_BLOCK_KEYS = frozenset(
    {
        "config_version",
        "application",
        "database",
        "redis",
        "health",
        "logging",
        "file_storage",
        "ytdlp",
        "oss",
        "cos",
        "llm",
        "asr",
        "embedding",
        "milvus",
        "deep_searcher",
        "mineru",
        "deer_flow",
        "langfuse",
        "alipay",
        "wechat_pay",
        "subscription",
        "oauth",
        "cors",
    }
)


def _yaml_section(raw: dict[str, Any], name: str) -> dict[str, Any]:
    block = raw.get(name)
    return block if isinstance(block, dict) else {}


def _merge_yaml_map(
    target: dict[str, Any],
    section: dict[str, Any],
    yaml_key_to_field: dict[str, str],
) -> None:
    for yaml_key, field_name in yaml_key_to_field.items():
        if yaml_key in section:
            target[field_name] = section[yaml_key]


def _flatten_yaml_tree(
    raw: dict[str, Any],
    field_names: frozenset[str],
) -> dict[str, Any]:
    """Map Deer Flow–style nested blocks to flat Settings field names."""
    out: dict[str, Any] = {}
    _merge_yaml_map(
        out,
        _yaml_section(raw, "application"),
        {
            "app_name": "app_name",
            "debug": "debug",
            "secret_key": "secret_key",
            "access_token_expire_minutes": "access_token_expire_minutes",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "database"),
        {
            "url": "database_url",
            "pool_size": "db_pool_size",
            "max_overflow": "db_max_overflow",
            "pool_timeout_seconds": "db_pool_timeout_seconds",
            "pool_recycle_seconds": "db_pool_recycle_seconds",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "redis"),
        {
            "redis_url": "redis_url",
            "celery_broker_url": "celery_broker_url",
            "celery_result_backend_url": "celery_result_backend_url",
            "cache_redis_url": "cache_redis_url",
            "task_event_redis_url": "task_event_redis_url",
            "task_event_channel_prefix": "task_event_channel_prefix",
            "generation_rate_limit_redis_url": "generation_rate_limit_redis_url",
            "generation_cooldown_seconds": "generation_cooldown_seconds",
            "generation_max_concurrent": "generation_max_concurrent",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "health"),
        {
            "healthcheck_timeout_seconds": "healthcheck_timeout_seconds",
            "readiness_include_external_dependencies": (
                "readiness_include_external_dependencies"
            ),
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "logging"),
        {
            "log_dir": "log_dir",
            "log_level": "log_level",
            "log_to_console": "log_to_console",
            "log_file_backup_count": "log_file_backup_count",
            "log_file_name": "log_file_name",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "file_storage"),
        {
            "upload_dir": "upload_dir",
            "max_upload_size_mb": "max_upload_size_mb",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "ytdlp"),
        {
            "ytdlp_cookies_file": "ytdlp_cookies_file",
            "ytdlp_subprocess_timeout_seconds": (
                "ytdlp_subprocess_timeout_seconds"
            ),
        },
    )
    # Aliyun OSS API is disabled; optional ``oss`` YAML block may only set
    # ``oss_path_prefix`` for legacy object_key layout on COS after migration.
    _merge_yaml_map(
        out,
        _yaml_section(raw, "oss"),
        {"oss_path_prefix": "oss_path_prefix"},
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "cos"),
        {
            "cos_secret_id": "config_cos_secret_id",
            "cos_secret_key": "config_cos_secret_key",
            "cos_region": "config_cos_region",
            "cos_bucket_name": "config_cos_bucket_name",
            "cos_path_prefix": "config_cos_path_prefix",
            "cos_public_base_url": "config_cos_public_base_url",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "llm"),
        {
            "dashscope_api_key": "dashscope_api_key",
            "dashscope_api_base": "dashscope_api_base",
            "litellm_model": "litellm_model",
            "litellm_vision_model": "litellm_vision_model",
            "litellm_image_model": "litellm_image_model",
            "dashscope_slide_image_edit_model": (
                "dashscope_slide_image_edit_model"
            ),
            "litellm_chat_router_enabled": "litellm_chat_router_enabled",
            "litellm_router_group_name": "litellm_router_group_name",
            "litellm_router_qwen_model": "litellm_router_qwen_model",
            "dashscope_api_key_secondary": "dashscope_api_key_secondary",
            "dashscope_api_base_secondary": "dashscope_api_base_secondary",
            "litellm_router_gemini_model": "litellm_router_gemini_model",
            "litellm_router_openai_model": "litellm_router_openai_model",
            "openai_api_key": "openai_api_key",
            "gemini_api_key": "gemini_api_key",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "asr"),
        {
            "qwen_asr_model": "qwen_asr_model",
            "qwen_asr_filetrans_model": "qwen_asr_filetrans_model",
            "qwen_asr_language": "qwen_asr_language",
            "qwen_asr_enable_itn": "qwen_asr_enable_itn",
            "qwen_asr_sync_max_file_mb": "qwen_asr_sync_max_file_mb",
            "qwen_asr_timeout_seconds": "qwen_asr_timeout_seconds",
            "qwen_asr_filetrans_timeout_seconds": (
                "qwen_asr_filetrans_timeout_seconds"
            ),
            "qwen_asr_poll_interval_seconds": "qwen_asr_poll_interval_seconds",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "embedding"),
        {
            "embedding_model": "embedding_model",
            "embedding_dimension": "embedding_dimension",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "deep_searcher"),
        {"deep_searcher_base_url": "deep_searcher_base_url"},
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "mineru"),
        {
            "mineru_base_url": "mineru_base_url",
            "mineru_api_key": "mineru_api_key",
            "mineru_parse_path": "mineru_parse_path",
            "mineru_timeout_seconds": "mineru_timeout_seconds",
            "mineru_oss_presign_seconds": "mineru_oss_presign_seconds",
            "mineru_use_multipart": "mineru_use_multipart",
            "mineru_model_version": "mineru_model_version",
            "mineru_poll_interval_seconds": "mineru_poll_interval_seconds",
            "mineru_parsed_assets_use_presigned_urls": (
                "mineru_parsed_assets_use_presigned_urls"
            ),
            "mineru_parsed_asset_presign_seconds": (
                "mineru_parsed_asset_presign_seconds"
            ),
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "deer_flow"),
        {
            "deer_flow_base_url": "deer_flow_base_url",
            "deer_flow_timeout_seconds": "deer_flow_timeout_seconds",
            "deer_flow_assistant_id": "deer_flow_assistant_id",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "langfuse"),
        {
            "langfuse_public_key": "langfuse_public_key",
            "langfuse_secret_key": "langfuse_secret_key",
            "langfuse_host": "langfuse_host",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "alipay"),
        {
            "alipay_notify_url": "alipay_notify_url",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "wechat_pay"),
        {
            "wechat_mch_id": "wechat_mch_id",
            "wechat_api_key": "wechat_api_key",
            "wechat_app_id": "wechat_app_id",
            "wechat_cert_serial_no": "wechat_cert_serial_no",
            "wechat_private_key_path": "wechat_private_key_path",
            "wechat_notify_url": "wechat_notify_url",
        },
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "subscription"),
        {
            "subscription_price_monthly": "subscription_price_monthly",
        },
    )
    oauth_keys = (
        "oauth_api_public_base_url",
        "frontend_oauth_redirect_base",
        "google_oauth_client_id",
        "google_oauth_client_secret",
        "weibo_oauth_app_key",
        "weibo_oauth_app_secret",
        "qq_oauth_app_id",
        "qq_oauth_app_key",
        "alipay_app_id",
        "alipay_private_key",
        "alipay_public_key",
        "alipay_gateway",
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "oauth"),
        {name: name for name in oauth_keys},
    )
    _merge_yaml_map(
        out,
        _yaml_section(raw, "cors"),
        {"cors_origins": "cors_origins"},
    )
    for key, val in raw.items():
        if key in _NESTED_BLOCK_KEYS:
            continue
        if key in field_names:
            out[key] = val
    return out


def _load_yaml_flattened(field_names: frozenset[str]) -> dict[str, Any]:
    """Parse config.yaml and return init kwargs for Settings."""
    path = _config_yaml_path()
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not loaded or not isinstance(loaded, dict):
        return {}
    expanded = _expand_env_recursive(loaded)
    return _flatten_yaml_tree(expanded, field_names)


class NotebookLmYamlSettingsSource(InitSettingsSource):
    """Lower priority than .env / process env; fills defaults from config.yaml."""

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        _ensure_dotenv_loaded()
        names = frozenset(settings_cls.model_fields.keys())
        data = _load_yaml_flattened(names)
        super().__init__(settings_cls, data)


def _strip_pem_markers(value: str) -> str:
    """Return the PEM body with all headers, footers, and whitespace removed."""
    body_lines = [
        line.strip()
        for line in value.splitlines()
        if line.strip() and not line.lstrip().startswith("-----")
    ]
    return "".join(body_lines)


def _wrap_pem_body(value: str, label: str) -> str:
    """Wrap a PEM body with the requested header/footer."""
    body = _strip_pem_markers(value)
    if not body:
        return ""
    chunks = [body[index : index + 64] for index in range(0, len(body), 64)]
    return (
        f"-----BEGIN {label}-----\n"
        f"{chr(10).join(chunks)}\n"
        f"-----END {label}-----"
    )


def _normalize_multiline_secret(value: str) -> str:
    """Normalize env-provided PEM content and escaped newlines."""
    normalized = value.strip().strip("\"'")
    if not normalized:
        return ""
    normalized = normalized.replace("\r", "").replace("\\n", "\n")
    if "-----BEGIN" in normalized:
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]
        return "\n".join(lines)
    return _strip_pem_markers(normalized)


def _normalize_alipay_private_key(value: str) -> str:
    """Convert Alipay private keys to PKCS#1 PEM for the SDK."""
    normalized = _normalize_multiline_secret(value)
    if not normalized:
        return ""

    candidates = [normalized]
    if "-----BEGIN" not in normalized:
        candidates = [
            _wrap_pem_body(normalized, "PRIVATE KEY"),
            _wrap_pem_body(normalized, "RSA PRIVATE KEY"),
        ]

    for candidate in candidates:
        try:
            private_key = serialization.load_pem_private_key(
                candidate.encode("utf-8"),
                password=None,
            )
        except (TypeError, ValueError):
            continue

        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pem.decode("utf-8").strip()

    return normalized


def _normalize_alipay_public_key(value: str) -> str:
    """Normalize Alipay public keys to PEM text."""
    normalized = _normalize_multiline_secret(value)
    if not normalized:
        return ""

    candidate = normalized
    if "-----BEGIN" not in normalized:
        candidate = _wrap_pem_body(normalized, "PUBLIC KEY")

    try:
        public_key = serialization.load_pem_public_key(candidate.encode("utf-8"))
    except ValueError:
        return candidate

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem.decode("utf-8").strip()


def _derive_public_key_from_private_key(private_key_pem: str) -> str | None:
    """Return the PEM public key that corresponds to a private key."""
    if not private_key_pem:
        return None
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None,
        )
    except (TypeError, ValueError):
        return None

    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return public_key.decode("utf-8").strip()


class Settings(BaseSettings):
    """Global application settings."""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        _ = dotenv_settings
        return (
            init_settings,
            env_settings,
            NotebookLmYamlSettingsSource(settings_cls),
            file_secret_settings,
        )

    # Application
    app_name: str = Field(
        default="NotebookLM",
        validation_alias=AliasChoices("APP_NAME"),
    )

    @field_validator("app_name")
    @classmethod
    def app_name_non_empty(cls, value: str) -> str:
        """FastAPI OpenAPI requires a non-empty title; blank env/YAML breaks boot."""
        cleaned = (value or "").strip()
        return cleaned or "NotebookLM"

    debug: bool = False
    secret_key: str = "change-me-to-a-real-secret-key"
    access_token_expire_minutes: int = 60 * 24

    # Database (MySQL for production)
    database_url: str = Field(
        validation_alias=AliasChoices("DATABASE_URL"),
    )
    db_pool_size: int = Field(
        default=20,
        validation_alias=AliasChoices("DB_POOL_SIZE"),
    )
    db_max_overflow: int = Field(
        default=20,
        validation_alias=AliasChoices("DB_MAX_OVERFLOW"),
    )
    db_pool_timeout_seconds: int = Field(
        default=30,
        validation_alias=AliasChoices("DB_POOL_TIMEOUT_SECONDS"),
    )
    db_pool_recycle_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices("DB_POOL_RECYCLE_SECONDS"),
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = Field(
        default="",
        validation_alias=AliasChoices("CELERY_BROKER_URL", "REDIS_BROKER_URL"),
    )
    celery_result_backend_url: str = Field(
        default="",
        validation_alias=AliasChoices(
            "CELERY_RESULT_BACKEND_URL",
            "REDIS_RESULT_BACKEND_URL",
        ),
    )
    cache_redis_url: str = Field(
        default="",
        validation_alias=AliasChoices("CACHE_REDIS_URL", "REDIS_CACHE_URL"),
    )
    task_event_redis_url: str = Field(
        default="",
        validation_alias=AliasChoices("TASK_EVENT_REDIS_URL", "REDIS_TASK_EVENT_URL"),
    )
    task_event_channel_prefix: str = "task-events"
    generation_rate_limit_redis_url: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GENERATION_RATE_LIMIT_REDIS_URL",
            "REDIS_GENERATION_RATE_LIMIT_URL",
        ),
    )
    generation_cooldown_seconds: int = Field(
        default=300,
        ge=1,
        le=86400,
        validation_alias=AliasChoices("GENERATION_COOLDOWN_SECONDS"),
    )
    generation_max_concurrent: int = Field(
        default=5,
        ge=1,
        le=100,
        validation_alias=AliasChoices("GENERATION_MAX_CONCURRENT"),
    )

    # Health checks
    healthcheck_timeout_seconds: float = 2.0
    readiness_include_external_dependencies: bool = False

    # Logging (file rotation at local midnight; mount LOG_DIR as a volume in
    # Docker so logs survive container removal)
    log_dir: str = Field(
        default="logs",
        validation_alias=AliasChoices("LOG_DIR"),
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL"),
    )
    log_to_console: bool = Field(
        default=True,
        validation_alias=AliasChoices("LOG_TO_CONSOLE"),
    )
    log_file_backup_count: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("LOG_FILE_BACKUP_COUNT"),
    )
    log_file_name: str = Field(
        default="app.log",
        validation_alias=AliasChoices("LOG_FILE_NAME"),
    )

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # yt-dlp: Netscape-format cookies (Bilibili subtitles often require login)
    ytdlp_cookies_file: str = Field(
        default="",
        validation_alias=AliasChoices(
            "YTDLP_COOKIES_FILE",
            "BILIBILI_COOKIES_FILE",
        ),
    )
    ytdlp_subprocess_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        validation_alias=AliasChoices(
            "YTDLP_SUBPROCESS_TIMEOUT_SECONDS",
        ),
    )

    # Legacy object key path prefix (former Aliyun OSS layout). Used only to
    # resolve historical object_key variants on COS; OSS SDK is not used.
    oss_path_prefix: str = Field(
        default="txt2imgcn",
        validation_alias=AliasChoices(
            "OSS_PATH_PREFIX",
            "oss_path_prefix",
        ),
    )

    # Tencent Cloud COS (preferred object storage). Values come only from the
    # ``cos`` block in ``config.yaml`` (after ``$VAR`` expansion). Process env
    # keys ``COS_*`` are intentionally not bound so they do not override YAML.
    config_cos_secret_id: str = ""
    config_cos_secret_key: str = ""
    config_cos_region: str = "ap-shanghai"
    config_cos_bucket_name: str = "notebooklm-1300396013"
    config_cos_path_prefix: str = "txt2imgcn"
    config_cos_public_base_url: str = (
        "https://notebooklm-1300396013.cos.ap-shanghai.myqcloud.com"
    )

    # LiteLLM：统一通过 SDK 调用大模型（Chat / Vision / Embedding）
    # DashScope 鉴权：LITELLM 使用 DASHSCOPE_API_KEY，兼容原 QWEN_API_KEY
    dashscope_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "QWEN_API_KEY"),
    )
    dashscope_api_base: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1",
        validation_alias=AliasChoices(
            "DASHSCOPE_API_BASE", "QWEN_API_BASE", "dashscope_api_base"
        ),
    )

    # SDK 模式：LITELLM_MODEL 如 dashscope/qwen3.5-plus、openrouter/...
    litellm_model: str = Field(
        default="dashscope/qwen3.5-plus",
        validation_alias=AliasChoices(
            "LITELLM_MODEL", "DEFAULT_LLM_MODEL", "litellm_model"
        ),
    )
    litellm_vision_model: str = Field(
        default="dashscope/qwen3-vl-plus",
        validation_alias=AliasChoices(
            "LITELLM_VISION_MODEL",
            "VISION_UNDERSTAND_MODEL",
            "litellm_vision_model",
        ),
    )
    # 图像生成：LiteLLM 暂未支持 DashScope 图像接口，仍用 DashScope 直连时的模型名
    litellm_image_model: str = Field(
        default="qwen-image-max",
        validation_alias=AliasChoices(
            "LITELLM_IMAGE_MODEL",
            "VISION_CREATE_MODEL",
            "litellm_image_model",
        ),
    )
    dashscope_slide_image_edit_model: str = Field(
        default="qwen-image-edit",
        validation_alias=AliasChoices(
            "DASHSCOPE_SLIDE_IMAGE_EDIT_MODEL",
            "dashscope_slide_image_edit_model",
        ),
    )

    # LiteLLM SDK Router（无需 Proxy）：虚拟名经 model_group_alias 指向 Qwen 池
    # （两路 simple-shuffle）；Qwen 均失败后按 fallbacks 依次尝试 Gemini、OpenAI。
    # 启用后请将 LITELLM_MODEL 设为与 LITELLM_ROUTER_GROUP_NAME 相同。
    litellm_chat_router_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "LITELLM_CHAT_ROUTER_ENABLED",
            "litellm_chat_router_enabled",
        ),
    )
    litellm_router_group_name: str = Field(
        default="notebooklm-chat",
        validation_alias=AliasChoices(
            "LITELLM_ROUTER_GROUP_NAME",
            "litellm_router_group_name",
        ),
    )
    litellm_router_qwen_model: str = Field(
        default="dashscope/qwen3.5-plus",
        validation_alias=AliasChoices(
            "LITELLM_ROUTER_QWEN_MODEL",
            "litellm_router_qwen_model",
        ),
    )
    dashscope_api_key_secondary: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DASHSCOPE_API_KEY_SECONDARY",
            "QWEN_API_KEY_SECONDARY",
            "dashscope_api_key_secondary",
        ),
    )
    dashscope_api_base_secondary: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DASHSCOPE_API_BASE_SECONDARY",
            "dashscope_api_base_secondary",
        ),
    )
    litellm_router_gemini_model: str = Field(
        default="gemini/gemini-3.1-pro-preview",
        validation_alias=AliasChoices(
            "LITELLM_ROUTER_GEMINI_MODEL",
            "litellm_router_gemini_model",
        ),
    )
    litellm_router_openai_model: str = Field(
        default="openai/gpt-5.4",
        validation_alias=AliasChoices(
            "LITELLM_ROUTER_OPENAI_MODEL",
            "litellm_router_openai_model",
        ),
    )
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "OPENAI_API_KEY",
            "openai_api_key",
        ),
    )
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "gemini_api_key",
        ),
    )

    qwen_asr_model: str = Field(
        default="dashscope/qwen3-asr-flash",
        validation_alias=AliasChoices(
            "QWEN_ASR_MODEL", "qwen_asr_model"
        ),
    )
    qwen_asr_filetrans_model: str = Field(
        default="dashscope/qwen3-asr-flash-filetrans",
        validation_alias=AliasChoices(
            "QWEN_ASR_FILETRANS_MODEL", "qwen_asr_filetrans_model"
        ),
    )
    qwen_asr_language: str = Field(
        default="",
        validation_alias=AliasChoices(
            "QWEN_ASR_LANGUAGE", "qwen_asr_language"
        ),
    )
    qwen_asr_enable_itn: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "QWEN_ASR_ENABLE_ITN", "qwen_asr_enable_itn"
        ),
    )
    qwen_asr_sync_max_file_mb: int = Field(
        default=10,
        validation_alias=AliasChoices(
            "QWEN_ASR_SYNC_MAX_FILE_MB", "qwen_asr_sync_max_file_mb"
        ),
    )
    qwen_asr_timeout_seconds: float = Field(
        default=120.0,
        validation_alias=AliasChoices(
            "QWEN_ASR_TIMEOUT_SECONDS", "qwen_asr_timeout_seconds"
        ),
    )
    qwen_asr_filetrans_timeout_seconds: float = Field(
        default=900.0,
        validation_alias=AliasChoices(
            "QWEN_ASR_FILETRANS_TIMEOUT_SECONDS",
            "qwen_asr_filetrans_timeout_seconds",
        ),
    )
    qwen_asr_poll_interval_seconds: float = Field(
        default=2.0,
        validation_alias=AliasChoices(
            "QWEN_ASR_POLL_INTERVAL_SECONDS",
            "qwen_asr_poll_interval_seconds",
        ),
    )

    @field_validator("dashscope_api_key", mode="before")
    @classmethod
    def coerce_dashscope_api_key(cls, v):
        """Allow missing/None as empty string."""
        return v if isinstance(v, str) else ""

    @field_validator(
        "dashscope_api_key_secondary",
        "dashscope_api_base_secondary",
        "openai_api_key",
        "gemini_api_key",
        mode="before",
    )
    @classmethod
    def coerce_litellm_router_string_fields(cls, v):
        """Allow missing/None as empty string."""
        return v if isinstance(v, str) else ""

    @field_validator("litellm_vision_model", mode="after")
    @classmethod
    def normalize_litellm_vision_model(cls, v: str) -> str:
        """LiteLLM requires a provider prefix (e.g. dashscope/qwen3-vl-plus).

        Config files often use the bare DashScope model id; map those so
        acompletion() and api_base injection in llm_router match.
        """
        v = (v or "").strip()
        if not v:
            return "dashscope/qwen3-vl-plus"
        if "/" in v:
            return v
        lower = v.lower()
        if lower.startswith("qwen") or lower.startswith("tongyi"):
            return f"dashscope/{v}"
        return v

    # Embedding：多模态向量（文本/图/视频），直连 DashScope MultiModalEmbedding
    embedding_model: str = "qwen3-vl-embedding"
    embedding_dimension: int = 1024

    # DeepSearcher：远程 HTTP（``/upload``, ``/load-files/``, ``/query/``）。
    # 原 Milvus 本地配置（milvus_uri / deep_search_max_iterations /
    # deep_search_top_k）已停用，见 config.yaml 注释块。
    deep_searcher_base_url: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias=AliasChoices(
            "DEEP_SEARCHER_BASE_URL",
            "deep_searcher_base_url",
        ),
    )

    # External MinerU HTTP service (PDF → Markdown + assets).
    mineru_base_url: str = Field(
        default="",
        validation_alias=AliasChoices(
            "MINERU_BASE_URL",
            "mineru_base_url",
        ),
    )
    mineru_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "MINERU_API_KEY",
            "mineru_api_key",
        ),
    )
    mineru_parse_path: str = Field(
        default="/v1/parse",
        validation_alias=AliasChoices(
            "MINERU_PARSE_PATH",
            "mineru_parse_path",
        ),
    )
    mineru_timeout_seconds: float = Field(
        default=600.0,
        ge=10.0,
        le=7200.0,
        validation_alias=AliasChoices(
            "MINERU_TIMEOUT_SECONDS",
            "mineru_timeout_seconds",
        ),
    )
    mineru_oss_presign_seconds: int = Field(
        default=7200,
        ge=60,
        le=604800,
        validation_alias=AliasChoices(
            "MINERU_OSS_PRESIGN_SECONDS",
            "mineru_oss_presign_seconds",
        ),
    )
    mineru_use_multipart: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "MINERU_USE_MULTIPART",
            "mineru_use_multipart",
        ),
    )
    # Official MinerU net API (POST /api/v4/extract/task): pipeline / vlm /
    # MinerU-HTML. Ignored when mineru_parse_path is not that endpoint.
    mineru_model_version: str = Field(
        default="vlm",
        validation_alias=AliasChoices(
            "MINERU_MODEL_VERSION",
            "mineru_model_version",
        ),
    )
    mineru_poll_interval_seconds: float = Field(
        default=3.0,
        ge=0.5,
        le=60.0,
        validation_alias=AliasChoices(
            "MINERU_POLL_INTERVAL_SECONDS",
            "mineru_poll_interval_seconds",
        ),
    )
    # Parsed PDF assets (images, etc.): presigned GET so browsers work on
    # private buckets. Set false only if the bucket is public-read and you
    # prefer short CDN-style URLs in stored markdown.
    mineru_parsed_assets_use_presigned_urls: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MINERU_PARSED_ASSETS_USE_PRESIGNED_URLS",
            "mineru_parsed_assets_use_presigned_urls",
        ),
    )
    mineru_parsed_asset_presign_seconds: int = Field(
        default=604800,
        ge=60,
        le=604800,
        validation_alias=AliasChoices(
            "MINERU_PARSED_ASSET_PRESIGN_SECONDS",
            "mineru_parsed_asset_presign_seconds",
        ),
    )

    # DeerFlow（Deep Research：本地默认与 deer-flow 网关端口一致）
    deer_flow_base_url: str = Field(
        default="http://localhost:2026",
        validation_alias=AliasChoices("DEER_FLOW_BASE_URL", "deer_flow_base_url"),
    )
    deer_flow_timeout_seconds: int = Field(
        default=600,
        validation_alias=AliasChoices(
            "DEER_FLOW_TIMEOUT_SECONDS",
            "deer_flow_timeout_seconds",
        ),
    )
    # DeerFlow LangGraph：注册图名（网关报错时会列出可用值，默认 lead_agent）
    deer_flow_assistant_id: str = Field(
        default="lead_agent",
        validation_alias=AliasChoices(
            "DEER_FLOW_ASSISTANT_ID",
            "deer_flow_assistant_id",
        ),
    )

    # Langfuse（本地或自托管时用于 @observe 等监控；留空则关闭，便于仅跑 Admin 等场景）
    langfuse_public_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LANGFUSE_PUBLIC_KEY", "langfuse_public_key"
        ),
    )
    langfuse_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LANGFUSE_SECRET_KEY", "langfuse_secret_key"
        ),
    )
    langfuse_host: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LANGFUSE_HOST", "LANGFUSE_BASE_URL", "langfuse_host"
        ),
    )

    # Alipay: app_id / keys / gateway load from ``oauth:`` in YAML (login + API);
    # ``alipay_notify_url`` loads from ``alipay:`` (payment callback only).
    alipay_app_id: str = Field(
        default="",
        validation_alias=AliasChoices("ALIPAY_APP_ID", "alipay_app_id"),
    )
    alipay_private_key: str = Field(
        default="",
        validation_alias=AliasChoices("ALIPAY_PRIVATE_KEY", "alipay_private_key"),
    )
    alipay_public_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "ALIPAY_PLATFORM_PUBLIC_KEY",
            "ALIPAY_PUBLIC_KEY",
            "alipay_public_key",
        ),
    )
    alipay_notify_url: str = Field(
        default="",
        validation_alias=AliasChoices("ALIPAY_NOTIFY_URL", "alipay_notify_url"),
    )
    alipay_gateway: str = Field(
        default="https://openapi.alipay.com/gateway.do",
        validation_alias=AliasChoices("ALIPAY_GATEWAY", "alipay_gateway"),
    )

    @field_validator("alipay_private_key", mode="before")
    @classmethod
    def normalize_alipay_private_key(cls, v):
        """Accept PKCS#8/PKCS#1 keys from single-line env vars."""
        return _normalize_alipay_private_key(v) if isinstance(v, str) else ""

    @field_validator("alipay_public_key", mode="before")
    @classmethod
    def normalize_alipay_public_key(cls, v):
        """Accept raw or PEM-formatted Alipay public keys."""
        return _normalize_alipay_public_key(v) if isinstance(v, str) else ""

    def validate_alipay_public_key_config(self) -> None:
        """Reject the common mistake of using the app public key."""
        if not self.alipay_private_key or not self.alipay_public_key:
            return

        app_public_key = _derive_public_key_from_private_key(
            self.alipay_private_key
        )
        if app_public_key and app_public_key == self.alipay_public_key.strip():
            raise ValueError(
                "ALIPAY_PUBLIC_KEY / ALIPAY_PLATFORM_PUBLIC_KEY must be the "
                "Alipay platform public key, not the app public key derived "
                "from ALIPAY_PRIVATE_KEY"
            )

    # WeChat Pay (Native QR code payment)
    wechat_mch_id: str = ""
    wechat_api_key: str = ""
    wechat_app_id: str = ""
    wechat_cert_serial_no: str = ""
    wechat_private_key_path: str = ""
    wechat_notify_url: str = ""

    # Subscription pricing (in cents / fen)
    subscription_price_monthly: int = 9900

    # OAuth (Google web login)
    # Public base URL the browser uses to reach this API (for IdP redirect_uri).
    oauth_api_public_base_url: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices(
            "OAUTH_API_PUBLIC_BASE_URL",
            "oauth_api_public_base_url",
        ),
    )
    # SPA origin for post-login redirect (?token= or ?error=).
    frontend_oauth_redirect_base: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices(
            "FRONTEND_OAUTH_REDIRECT_BASE",
            "frontend_oauth_redirect_base",
        ),
    )
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    # Weibo OAuth (https://open.weibo.com/apps)
    weibo_oauth_app_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "WEIBO_OAUTH_APP_KEY",
            "weibo_oauth_app_key",
        ),
    )
    weibo_oauth_app_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "WEIBO_OAUTH_APP_SECRET",
            "weibo_oauth_app_secret",
        ),
    )

    # QQ Connect (https://connect.qq.com/manage.html)
    qq_oauth_app_id: str = ""
    qq_oauth_app_key: str = ""

    # CORS (include http://localhost for Docker access via nginx port 80)
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept a JSON string or a Python list."""
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


_ensure_dotenv_loaded()
settings = Settings()
