"""
Shared test fixtures and configuration for ob1 tests.

This file is automatically discovered by pytest and makes fixtures
available to all test files.
"""
import asyncio
import pytest
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

# ============================================================================
# ASYNC FIXTURES
# ============================================================================

@pytest.fixture
async def mock_httpx_client() -> AsyncMock:
    """
    Mock httpx.AsyncClient for testing without real HTTP calls.

    Usage:
        async def test_api_call(mock_httpx_client):
            mock_httpx_client.post.return_value = httpx.Response(200, json={"status": "ok"})
    """
    return AsyncMock()


# ============================================================================
# GITHUB API FIXTURES
# ============================================================================

@pytest.fixture
def github_token() -> str:
    """Mock GitHub token for testing."""
    return "ghp_test_token_12345"


@pytest.fixture
def mock_github_response() -> Dict[str, Any]:
    """Sample GitHub API response for testing."""
    return {
        "number": 123,
        "title": "Test PR",
        "state": "open",
        "html_url": "https://github.com/owner/repo/pull/123",
        "head": {"ref": "feature-branch"},
        "base": {"ref": "main"}
    }


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def test_settings() -> Dict[str, str]:
    """Test configuration settings."""
    return {
        "GITHUB_TOKEN": "ghp_test_token",
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "DEFAULT_MODEL": "claude-sonnet-4-5"
    }


# ============================================================================
# FILE SYSTEM FIXTURES
# ============================================================================

@pytest.fixture
def temp_repo_dir(tmp_path: Path) -> Path:
    """Create a temporary directory simulating a git repository."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    return repo_dir


@pytest.fixture
def sample_diff() -> str:
    """Sample git diff for testing."""
    return """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
+    return True
"""


# ============================================================================
# ASYNC HELPER FUNCTIONS
# ============================================================================

def async_return(result):
    """Helper to create async functions that return a specific value."""
    async def _async_return(*args, **kwargs):
        return result
    return _async_return


def async_raise(exception):
    """Helper to create async functions that raise exceptions."""
    async def _async_raise(*args, **kwargs):
        raise exception
    return _async_raise
