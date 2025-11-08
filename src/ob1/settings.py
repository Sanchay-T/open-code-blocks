from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: Optional[str] = Field(None, alias="GITHUB_TOKEN")
    claude_api_key: Optional[str] = Field(None, alias="CLAUDE_API_KEY")
    cursor_api_key: Optional[str] = Field(None, alias="CURSOR_API_KEY")
    codex_api_key: Optional[str] = Field(None, alias="CODEX_API_KEY")


@lru_cache()
def get_settings(env_file: Optional[Path] = None) -> Settings:
    if env_file:
        return Settings(_env_file=env_file)
    return Settings()
