from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Values are read from a local .env file when it exists.
    The real .env file must never be committed to GitHub.
    """

    app_mode: Literal["demo", "openai"] = "demo"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    app_name: str = "Day 8 Job Match Agent"
    max_input_characters: int = Field(default=20_000, ge=1_000, le=100_000)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Create and cache one Settings object.

    Caching means the application does not repeatedly reload the .env file.
    """
    return Settings()