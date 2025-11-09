from pathlib import Path

import pytest
from rich.console import Console

pytest.importorskip("openai")

from ob1.providers.codex import CodexProvider


def _provider() -> CodexProvider:
    return CodexProvider(api_key="test-key", console=Console(record=True))


def test_diff_from_file_blocks_generates_unified_diff(tmp_path) -> None:
    repo_root = Path(tmp_path)
    target_file = repo_root / "frontend" / "src" / "App.jsx"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("import './App.css'\n\nfunction App() {\n  return null\n}\n")

    content = """
+ frontend/src/App.jsx
+ ```jsx
+ import { useState } from 'react';
+ import './App.css';
+ 
+ function App() {
+   const [value, setValue] = useState('');
+   return <div>{value}</div>;
+ }
+ ```
"""

    provider = _provider()
    diff_text = provider._diff_from_file_blocks(content, repo_root)

    assert diff_text is not None
    assert "--- a/frontend/src/App.jsx" in diff_text
    assert "++ import { useState }" in diff_text
