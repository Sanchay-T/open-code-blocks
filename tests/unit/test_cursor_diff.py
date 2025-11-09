from pathlib import Path

from ob1.providers.cursor import _sanitize_cursor_diff


def test_sanitize_cursor_diff_drops_incomplete_blocks() -> None:
    raw = """diff --git a/frontend/App.tsx b/frontend/App.tsx
--- a/frontend/App.tsx
+++ b/frontend/App.tsx
@@ -1 +1 @@
-console.log('foo')
+console.log('bar')

diff --git a/frontend/Broken.tsx b/frontend/Broken.tsx
--- a/frontend/Broken.tsx
+++ b/frontend/Broken.tsx
missing hunk header
"""
    sanitized, dropped = _sanitize_cursor_diff(raw.replace("\n", "\r\n"), Path("/repo"))

    assert "frontend/App.tsx" in sanitized
    assert sanitized.endswith("\n")
    assert len(dropped) == 1
    assert "Broken.tsx" in dropped[0]


def test_sanitize_cursor_diff_adds_missing_headers() -> None:
    raw = """--- a/frontend/Login.tsx
+++ b/frontend/Login.tsx
@@ -1 +1 @@
-foo
+bar
"""
    sanitized, dropped = _sanitize_cursor_diff(raw, Path("/repo"))

    assert sanitized.startswith("diff --git a/frontend/Login.tsx b/frontend/Login.tsx")
    assert not dropped


def test_sanitize_cursor_diff_normalizes_absolute_paths() -> None:
    raw = """diff --git /tmp/worktree/frontend/App.tsx /tmp/worktree/frontend/App.tsx
--- /tmp/worktree/frontend/App.tsx
+++ /tmp/worktree/frontend/App.tsx
@@ -1 +1 @@
-foo
+bar
"""
    sanitized, dropped = _sanitize_cursor_diff(raw, Path("/tmp/worktree"))

    assert sanitized.startswith("diff --git a/frontend/App.tsx b/frontend/App.tsx")
    assert not dropped


def test_sanitize_cursor_diff_adds_context_prefixes() -> None:
    raw = """diff --git a/frontend/src/App.jsx b/frontend/src/App.jsx
--- a/frontend/src/App.jsx
+++ b/frontend/src/App.jsx
@@ -1 +1,2 @@
function App() {
+  return null
}
"""
    sanitized, _ = _sanitize_cursor_diff(raw, Path("/repo"))

    lines = sanitized.splitlines()
    assert " function App() {" in lines
    assert "+  return null" in lines
