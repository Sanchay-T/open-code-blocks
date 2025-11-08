from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .git_ops import run_git
from .path_filters import matches_any


class ChangeGuardError(RuntimeError):
    pass


def list_changed_files(worktree: Path) -> List[str]:
    """Return paths (POSIX) with staged/unstaged changes."""

    out = run_git("status", "--porcelain", cwd=worktree)
    files: List[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path_part = line[3:].lstrip()
        # Handle renames "R  a -> b"
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        files.append(path_part)
    return files


def ensure_changes_within_scope(files: Iterable[str], allowed_patterns: Iterable[str]) -> None:
    patterns = list(allowed_patterns)
    if not patterns:
        return
    bad = [path for path in files if not matches_any(path, patterns)]
    if bad:
        raise ChangeGuardError(
            "Changes outside allowed scope detected: " + ", ".join(bad)
        )
