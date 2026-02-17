"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Global application settings."""

    # Application
    app_name: str = "NotebookLM Clone"
    debug: bool = False
    secret_key: str = "change-me-to-a-real-secret-key"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Database (MySQL for production)
    database_url: str = "mysql+aiomysql://abc123:A12345678b_@rm-uf689w29v133d5tuumo.mysql.rds.aliyuncs.com:3306/notebookLM"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # OBS (Object Storage Service, S3-compatible)
    obs_endpoint: str = "https://obs.cn-east-273.antacloud.com"
    obs_access_key: str = "RDIOYVKVX4UVFODZNRIB"
    obs_secret_key: str = "vLA01VVBGJ7XRFDWRkZX6KI3yGvsyqgA24Ofv09p"
    obs_bucket_name: str = "obs-antaai-t-az2"
    obs_path_prefix: str = "txt2imgcn"

    # LLM
    llm_api_base: str = "https://ai.anta.com/aimodels-server/private/llm/v1"
    llm_api_key: str = "d7d3c7896894a7e127b61fc1d676f217"
    default_llm_model: str = "qwen3-max"
    slide_content_model: str = "qwen3-max"
    slide_image_model: str = "qwen-image-max"

    # Qwen-Image (text-to-image) API, e.g. DashScope
    qwen_image_api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    qwen_image_api_key: str = os.getenv("QWEN_IMAGE_API_KEY") # from env QWEN_IMAGE_API_KEY

    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
