from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .path_filters import matches_any


@dataclass
class RepoContext:
    file_snippets: List[str]
    package_summary: str


def gather_repo_context(
    worktree: Path,
    patterns: Iterable[str],
    max_files: int = 8,
    max_chars_per_file: int = 600,
) -> RepoContext:
    matched_files: List[Path] = []
    ignore_roots = {".git", ".ob1", "node_modules"}
    for path in sorted(worktree.rglob("*")):
        if len(matched_files) >= max_files:
            break
        if not path.is_file():
            continue
        rel = path.relative_to(worktree).as_posix()
        if any(part in ignore_roots for part in rel.split("/")):
            continue
        if matches_any(rel, patterns):
            matched_files.append(path)

    snippets: List[str] = []
    for path in matched_files:
        rel = path.relative_to(worktree).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        snippet = text[:max_chars_per_file]
        snippets.append(f"### {rel}\n````text\n{snippet}\n````")

    package_summary = _summarize_package_json(worktree)
    return RepoContext(file_snippets=snippets, package_summary=package_summary)


def _summarize_package_json(worktree: Path) -> str:
    pkg_path = worktree / "frontend" / "package.json"
    if not pkg_path.exists():
        return ""
    try:
        data = json.loads(pkg_path.read_text())
    except json.JSONDecodeError:
        return ""
    name = data.get("name", "frontend")
    scripts = data.get("scripts", {})
    important_scripts = {k: scripts[k] for k in ["dev", "build", "preview"] if k in scripts}
    deps = list(data.get("dependencies", {}).keys())[:6]
    return (
        f"Package `{name}` scripts: {important_scripts}. Key deps: {', '.join(deps) if deps else 'n/a'}."
    )


def build_prompt_text(task: str, scope_patterns: Iterable[str], context: RepoContext) -> str:
    scope_text = ", ".join(scope_patterns)
    file_section = "\n\n".join(context.file_snippets)
    package_section = context.package_summary
    instructions = f"""
You are ob1, an elite frontend engineer. Implement the user request inside the allowed scope only.

Task:
{task}

Constraints:
- Only edit files matching: {scope_text}
- Changes must be buildable via `npm install && npm run build` inside `frontend/`.
- Keep code clean, typed (where relevant), and ensure responsive design.
- If a new page/component is created, update routing or App.jsx so it renders.

Project Summary:
{package_section}

Important Files:
{file_section}

Deliverables:
1. Implement the feature completely, including UI and minimal styling.
2. Provide client-side validation and friendly error states.
3. Keep copy concise and professional.

When finished, ensure `npm run build` would succeed. Do not remove unrelated code.
"""
    return instructions.strip()
