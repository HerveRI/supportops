from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "SupportOps API"
    app_environment: str = "development"
    debug: bool = False
    database_url: str

    auth_secret_key: str
    access_token_expire_minutes: int = 30
    auth_cookie_name: str = "supportops_access_token"
    auth_cookie_secure: bool = False

    frontend_origin: str = "http://localhost:5173"

    document_storage_dir: Path = Path("storage/documents")
    max_document_size_bytes: int = 5 * 1024 * 1024

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
