import pytest
from rich.console import Console
from unidiff import PatchSet

pytest.importorskip("openai")

from ob1.providers.codex import CodexProvider


def _make_provider() -> CodexProvider:
    return CodexProvider(api_key="test-key", console=Console(record=True))


def test_validate_scope_flags_disallowed_paths() -> None:
    provider = _make_provider()
    diff = """diff --git a/frontend/App.tsx b/frontend/App.tsx
--- a/frontend/App.tsx
+++ b/frontend/App.tsx
@@ -1 +1 @@
-foo
+bar
diff --git a/backend/api.ts b/backend/api.ts
--- a/backend/api.ts
+++ b/backend/api.ts
@@ -1 +1 @@
-foo
+bar
"""
    patch = PatchSet(diff)

    message = provider._validate_scope(patch, ["frontend/**"])
    assert message is not None
    assert "backend/api.ts" in message


def test_validate_scope_passes_when_only_allowed_paths() -> None:
    provider = _make_provider()
    diff = """diff --git a/frontend/App.tsx b/frontend/App.tsx
--- a/frontend/App.tsx
+++ b/frontend/App.tsx
@@ -1 +1 @@
-foo
+bar
"""
    patch = PatchSet(diff)

    message = provider._validate_scope(patch, ["frontend/**"])
    assert message is None


def test_scope_guard_disabled_for_global_scope() -> None:
    provider = _make_provider()

    assert not provider._scope_guard_enabled(["**"])
    assert provider._scope_guard_enabled(["**", "frontend/**"])
