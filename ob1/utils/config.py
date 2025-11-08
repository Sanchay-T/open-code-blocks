"""
Configuration management for ob1.

Handles loading and validation of configuration from environment variables
and .env files.
"""
import os
from pathlib import Path
from typing import Dict, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Required settings:
        - GITHUB_TOKEN: GitHub personal access token (must start with 'ghp_' or 'github_pat_')
        - ANTHROPIC_API_KEY: Anthropic API key (must start with 'sk-ant-')

    Optional settings:
        - DEFAULT_MODEL: Claude model to use (default: claude-sonnet-4-5)
        - MAX_PARALLEL: Maximum parallel agents (default: 5)
        - TIMEOUT: Timeout in seconds (default: 600)

    Example:
        >>> config = Config.load()
        >>> print(config.github_token)
        'ghp_...'
    """

    # Required settings
    github_token: str = Field(..., description="GitHub personal access token")
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")

    # Optional settings with defaults
    default_model: str = Field(
        default="claude-sonnet-4-5",
        description="Default Claude model to use"
    )
    max_parallel: int = Field(
        default=5,
        description="Maximum number of parallel agents",
        gt=0  # Must be greater than 0
    )
    timeout: int = Field(
        default=600,
        description="Timeout for agent execution in seconds",
        gt=0
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore unknown env vars
    )

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: str) -> str:
        """Validate GitHub token format and non-emptiness."""
        # Strip whitespace
        v = v.strip()

        # Check not empty
        if not v:
            raise ValueError("GITHUB_TOKEN cannot be empty")

        # Check valid prefix
        if not (v.startswith("ghp_") or v.startswith("github_pat_")):
            raise ValueError(
                "GITHUB_TOKEN must start with 'ghp_' or 'github_pat_'"
            )

        return v

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format and non-emptiness."""
        # Strip whitespace
        v = v.strip()

        # Check not empty
        if not v:
            raise ValueError("ANTHROPIC_API_KEY cannot be empty")

        # Check valid prefix
        if not v.startswith("sk-ant-"):
            raise ValueError("ANTHROPIC_API_KEY must start with 'sk-ant-'")

        return v

    @field_validator("default_model")
    @classmethod
    def strip_default_model(cls, v: str) -> str:
        """Strip whitespace from default model."""
        return v.strip()

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from environment variables.

        Returns:
            Config: Loaded and validated configuration

        Raises:
            ConfigError: If required settings are missing or invalid

        Example:
            >>> config = Config.load()
            >>> assert config.is_valid()
        """
        try:
            return cls()
        except Exception as e:
            error_msg = str(e)

            # Parse pydantic validation errors and make them user-friendly
            if "validation error" in error_msg.lower():
                # Check for specific field errors
                if "github_token" in error_msg.lower():
                    if "field required" in error_msg.lower():
                        raise ConfigError(
                            "GITHUB_TOKEN environment variable is required"
                        ) from e

                if "anthropic_api_key" in error_msg.lower():
                    if "field required" in error_msg.lower():
                        raise ConfigError(
                            "ANTHROPIC_API_KEY environment variable is required"
                        ) from e

                if "max_parallel" in error_msg.lower():
                    if "unable to parse" in error_msg.lower() or "int_parsing" in error_msg.lower():
                        raise ConfigError(
                            "MAX_PARALLEL must be an integer"
                        ) from e
                    if "greater than 0" in error_msg.lower():
                        raise ConfigError(
                            "MAX_PARALLEL must be positive"
                        ) from e

            # Generic error for validation issues
            if "GITHUB_TOKEN" not in error_msg and "github_token" in error_msg:
                error_msg = error_msg.replace("github_token", "GITHUB_TOKEN")
            if "ANTHROPIC_API_KEY" not in error_msg and "anthropic_api_key" in error_msg:
                error_msg = error_msg.replace("anthropic_api_key", "ANTHROPIC_API_KEY")

            raise ConfigError(error_msg) from e

    @classmethod
    def load_from_file(cls, file_path: str) -> "Config":
        """
        Load configuration from a .env file.

        Args:
            file_path: Path to .env file

        Returns:
            Config: Loaded and validated configuration

        Raises:
            ConfigError: If file not found or config invalid

        Example:
            >>> config = Config.load_from_file('.env.production')
        """
        path = Path(file_path)

        if not path.exists():
            raise ConfigError(f"Config file not found: {file_path}")

        try:
            # Load env vars from file into environment
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

            return cls.load()
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(f"Error loading config from file: {e}") from e

    def is_valid(self) -> bool:
        """
        Check if configuration is valid.

        Returns:
            bool: True if valid, False otherwise

        Example:
            >>> config = Config.load()
            >>> if config.is_valid():
            ...     print("Config OK!")
        """
        try:
            # Validate all fields
            assert self.github_token
            assert self.anthropic_api_key
            assert self.max_parallel > 0
            assert self.timeout > 0
            return True
        except (AssertionError, AttributeError):
            return False

    def to_dict(self, mask_secrets: bool = False) -> Dict[str, any]:
        """
        Convert configuration to dictionary.

        Args:
            mask_secrets: If True, mask sensitive values (tokens, API keys)

        Returns:
            dict: Configuration as dictionary

        Example:
            >>> config = Config.load()
            >>> safe_dict = config.to_dict(mask_secrets=True)
            >>> print(safe_dict['github_token'])
            'ghp_***'
        """
        data = {
            "github_token": self.github_token,
            "anthropic_api_key": self.anthropic_api_key,
            "default_model": self.default_model,
            "max_parallel": self.max_parallel,
            "timeout": self.timeout,
        }

        if mask_secrets:
            # Mask sensitive values - show only prefix
            if data["github_token"]:
                prefix = data["github_token"].split("_")[0] + "_"
                data["github_token"] = prefix + "***"

            if data["anthropic_api_key"]:
                data["anthropic_api_key"] = "sk-ant-***"

        return data
