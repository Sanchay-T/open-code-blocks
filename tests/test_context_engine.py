from pathlib import Path

from ob1.context_engine import build_prompt_text, gather_repo_context


def test_gather_repo_context(tmp_path):
    frontend = tmp_path / "frontend" / "src"
    frontend.mkdir(parents=True)
    app = frontend / "App.jsx"
    app.write_text("function App() { return <div>Hello</div>; }\n")
    pkg = tmp_path / "frontend" / "package.json"
    pkg.write_text('{"name": "frontend", "scripts": {"dev": "vite"}}')

    ctx = gather_repo_context(tmp_path, ["frontend/**"], max_files=2)
    assert ctx.file_snippets
    prompt = build_prompt_text("Add login", ["frontend/**"], ctx)
    assert "Add login" in prompt
    assert "frontend" in prompt
