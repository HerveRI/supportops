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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
