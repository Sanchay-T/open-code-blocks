"""
Unit tests for configuration management.

Following TDD: These tests are written BEFORE implementation.
The ob1.utils.config module doesn't exist yet - tests will fail (RED phase).
"""
import pytest
from unittest.mock import patch
import os

# This import will fail - config.py doesn't exist yet
from ob1.utils.config import Config, ConfigError


class TestConfigLoading:
    """Test configuration loading from environment variables."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_load_config_from_env_vars(self):
        """Test that config loads successfully from environment variables."""
        config = Config.load()

        assert config.github_token == "ghp_test123"
        assert config.anthropic_api_key == "sk-ant-test456"

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
        "DEFAULT_MODEL": "claude-opus-4",
    })
    def test_load_config_with_optional_settings(self):
        """Test that optional settings are loaded when present."""
        config = Config.load()

        assert config.default_model == "claude-opus-4"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_with_defaults(self):
        """Test that default values are used when env vars not set."""
        # This should use defaults for optional settings
        # But will fail for required settings
        with pytest.raises(ConfigError, match="GITHUB_TOKEN"):
            Config.load()


class TestConfigValidation:
    """Test configuration validation."""

    @patch.dict(os.environ, {"GITHUB_TOKEN": "", "ANTHROPIC_API_KEY": "sk-ant-test"})
    def test_empty_github_token_raises_error(self):
        """Test that empty GitHub token raises validation error."""
        with pytest.raises(ConfigError, match="GITHUB_TOKEN.*empty"):
            Config.load()

    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test", "ANTHROPIC_API_KEY": ""})
    def test_empty_anthropic_key_raises_error(self):
        """Test that empty Anthropic API key raises validation error."""
        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY.*empty"):
            Config.load()

    @patch.dict(os.environ, {"GITHUB_TOKEN": "invalid_prefix_123", "ANTHROPIC_API_KEY": "sk-ant-test"})
    def test_invalid_github_token_format(self):
        """Test that GitHub token with invalid prefix is rejected."""
        with pytest.raises(ConfigError, match="GITHUB_TOKEN.*must start with 'ghp_' or 'github_pat_'"):
            Config.load()

    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test", "ANTHROPIC_API_KEY": "invalid_prefix"})
    def test_invalid_anthropic_key_format(self):
        """Test that Anthropic API key with invalid prefix is rejected."""
        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY.*must start with 'sk-ant-'"):
            Config.load()


class TestConfigDefaults:
    """Test default configuration values."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_default_model_is_claude_sonnet(self):
        """Test that default model is claude-sonnet-4-5."""
        config = Config.load()

        assert config.default_model == "claude-sonnet-4-5"

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_default_max_parallel_agents(self):
        """Test that default max parallel agents is 5."""
        config = Config.load()

        assert config.max_parallel == 5

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_default_timeout(self):
        """Test that default timeout is 600 seconds."""
        config = Config.load()

        assert config.timeout == 600


class TestConfigProperties:
    """Test configuration properties and methods."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_config_is_valid_returns_true(self):
        """Test that is_valid() returns True for valid config."""
        config = Config.load()

        assert config.is_valid() is True

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_config_to_dict(self):
        """Test that config can be converted to dictionary."""
        config = Config.load()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "github_token" in config_dict
        assert "anthropic_api_key" in config_dict
        assert "default_model" in config_dict

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
    })
    def test_config_to_dict_masks_secrets(self):
        """Test that to_dict() masks sensitive values."""
        config = Config.load()
        config_dict = config.to_dict(mask_secrets=True)

        assert config_dict["github_token"] == "ghp_***"
        assert config_dict["anthropic_api_key"] == "sk-ant-***"


class TestConfigFromFile:
    """Test loading configuration from file."""

    def test_load_from_env_file(self, tmp_path):
        """Test loading config from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GITHUB_TOKEN=ghp_from_file\n"
            "ANTHROPIC_API_KEY=sk-ant-from_file\n"
            "DEFAULT_MODEL=claude-opus-4\n"
        )

        config = Config.load_from_file(str(env_file))

        assert config.github_token == "ghp_from_file"
        assert config.anthropic_api_key == "sk-ant-from_file"
        assert config.default_model == "claude-opus-4"

    def test_load_from_nonexistent_file_raises_error(self):
        """Test that loading from nonexistent file raises error."""
        with pytest.raises(ConfigError, match="Config file not found"):
            Config.load_from_file("/nonexistent/path/.env")


class TestConfigEdgeCases:
    """Test edge cases and error handling."""

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "  ghp_test123  ",
        "ANTHROPIC_API_KEY": "  sk-ant-test456  ",
    })
    def test_config_strips_whitespace(self):
        """Test that config values have whitespace stripped."""
        config = Config.load()

        assert config.github_token == "ghp_test123"
        assert config.anthropic_api_key == "sk-ant-test456"

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
        "MAX_PARALLEL": "invalid",
    })
    def test_invalid_integer_setting_raises_error(self):
        """Test that invalid integer value raises error."""
        with pytest.raises(ConfigError, match="MAX_PARALLEL.*must be an integer"):
            Config.load()

    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_test123",
        "ANTHROPIC_API_KEY": "sk-ant-test456",
        "MAX_PARALLEL": "0",
    })
    def test_zero_max_parallel_raises_error(self):
        """Test that max_parallel must be positive."""
        with pytest.raises(ConfigError, match="MAX_PARALLEL.*must be positive"):
            Config.load()
