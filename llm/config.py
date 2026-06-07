from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- DashScope / OpenAI 兼容 ---
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field(default="qwen-plus", alias="LLM_MODEL")

    # --- DeepSeek ---
    ds_api_key: str = Field(default="", alias="DS_API_KEY")
    ds_base_url: str = Field(
        default="https://api.deepseek.com",
        alias="DS_BASE_URL",
    )
    ds_model: str = Field(default="deepseek-v4-pro", alias="DS_MODEL")

    admin_token: str = Field(default="", alias="ADMIN_TOKEN")
    frontend_origin: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_ORIGIN")

    db_host: str = Field(default="127.0.0.1", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(default="root", alias="DB_USER")
    db_password: str = Field(default="Root@123456", alias="DB_PASSWORD")
    db_name: str = Field(default="agent_workflow", alias="DB_NAME")

    @property
    def database_url(self) -> str:
        db_user = quote_plus(self.db_user)
        db_password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{db_user}:{db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.llm_api_key and not settings.ds_api_key:
        raise RuntimeError(
            "Missing required env variable: LLM_API_KEY or DS_API_KEY "
            "(at least one must be configured)"
        )
    return settings


settings = get_settings()

LLM_API_KEY = settings.llm_api_key
LLM_BASE_URL = settings.llm_base_url
LLM_MODEL = settings.llm_model

ADMIN_TOKEN = settings.admin_token
FRONTEND_ORIGIN = settings.frontend_origin
