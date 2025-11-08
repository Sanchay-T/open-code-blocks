from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _discover_env_file() -> Optional[Path]:
    cwd = Path.cwd()
    for path in (cwd, *cwd.parents):
        candidate = path / ".env"
        if candidate.exists():
            return candidate
    return None


def _gh_cli_token() -> Optional[str]:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
        token = result.stdout.strip()
        return token or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    github_token: Optional[str] = Field(None, alias="GITHUB_TOKEN")
    claude_api_key: Optional[str] = Field(None, alias="CLAUDE_API_KEY")
    cursor_api_key: Optional[str] = Field(None, alias="CURSOR_API_KEY")
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    codex_cli_key: Optional[str] = Field(None, alias="CODEX_CLI_KEY")


@lru_cache()
def get_settings(env_file: Optional[Path] = None) -> Settings:
    env_source = env_file or _discover_env_file()
    kwargs = {}
    if env_source:
        kwargs["_env_file"] = env_source
    settings = Settings(**kwargs)
    if not settings.github_token:
        token = _gh_cli_token()
        if token:
            settings.github_token = token
    if not settings.openai_api_key and settings.codex_cli_key:
        settings.openai_api_key = settings.codex_cli_key
    return settings
