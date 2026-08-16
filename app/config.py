from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    hf_token: str = ""
    # HF free-tier model availability shifts over time — verified working
    # via HF's router as of this writing. If this starts 400ing with
    # "not supported by any provider", swap to another current chat model.
    hf_model: str = "Qwen/Qwen2.5-7B-Instruct"
    hf_timeout_seconds: float = 30.0

    api_key: str = "change-me"

    # Comma-separated origins allowed to call the API from a browser (the
    # React dev server). Not a new architectural layer — just what's needed
    # for the frontend in frontend/ to reach this API cross-origin.
    cors_origins: str = "http://localhost:5173"

    # 127.0.0.1, not "localhost": avoids libpq trying the IPv6 (::1) address
    # first and doubling the wait (connect_timeout applies per address).
    database_url: str = "postgresql://sakhi:sakhi@127.0.0.1:5432/sakhi"

    max_tool_iterations: int = 3
    max_message_length: int = 2000

    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
