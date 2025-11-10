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
    max_files: int = 20,  # Increased from 8
    max_chars_per_file: int = 2000,  # Increased from 600
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
You are ob1, an elite frontend engineer tasked with implementing features with production-level quality.

Task:
{task}

Constraints:
- Only edit files matching: {scope_text}
- Changes must be buildable via `npm install && npm run build` inside `frontend/`.
- Keep code clean, properly typed (TypeScript/JSDoc), and ensure responsive design.
- If a new page/component is created, update routing configuration so it's accessible.
- IMPORTANT: Create Playwright test files for any new routes or significant features.

Project Summary:
{package_section}

Current Codebase Context:
{file_section}

Critical Requirements:
1. **Code Quality**: Write clean, maintainable code following existing patterns in the codebase.
2. **Complete Implementation**: Implement the full feature including UI, logic, validation, and error handling.
3. **Routing Integration**: If adding new pages, ensure they're properly integrated into the routing system (React Router, etc.).
4. **Test Coverage**: For new routes/features, create Playwright tests in `frontend/tests/` directory:
   - Test file naming: `<feature-name>.spec.ts`
   - Test critical user flows (navigation, form submission, error states)
   - Include proper assertions for UI elements
5. **Consistency**: Maintain styling consistency with existing components.
6. **Build Validation**: Ensure `npm run build` succeeds after changes.

Structure Guidelines:
- Components: Place in `frontend/src/components/` (organized by feature if appropriate)
- Pages: Place in `frontend/src/pages/` or appropriate routing directory
- Tests: Place in `frontend/tests/` with descriptive names
- Styles: Follow existing styling approach (CSS modules, Tailwind, etc.)

Never:
- Remove or break existing unrelated functionality
- Create routes that don't exist (like /dashboard/root without implementing /dashboard first)
- Leave incomplete implementations
- Skip error handling or loading states

When finished, the application should:
- Build successfully (`npm run build`)
- Have working routing to all new pages
- Include basic test coverage for new features
- Maintain visual consistency with existing UI
"""
    return instructions.strip()
