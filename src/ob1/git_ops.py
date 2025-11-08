from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


class GitError(RuntimeError):
    pass


def run_git(*args: str, cwd: Optional[Path] = None) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.STDOUT)
        return out.decode().strip()
    except subprocess.CalledProcessError as e:
        raise GitError(e.output.decode().strip()) from e


def is_repo(path: Path | None = None) -> bool:
    path = path or Path.cwd()
    try:
        run_git("rev-parse", "--is-inside-work-tree", cwd=path)
        return True
    except GitError:
        return False


def current_branch(cwd: Optional[Path] = None) -> Optional[str]:
    try:
        return run_git("branch", "--show-current", cwd=cwd) or None
    except GitError:
        return None


def has_remote(name: str = "origin", cwd: Optional[Path] = None) -> bool:
    try:
        out = run_git("remote", cwd=cwd)
        return name in out.splitlines()
    except GitError:
        return False


def get_origin_url(cwd: Optional[Path] = None, remote: str = "origin") -> str:
    try:
        return run_git("config", f"remote.{remote}.url", cwd=cwd)
    except GitError as e:
        raise GitError(f"Remote '{remote}' not found: {e}") from e


def add_worktree(path: Path, branch: str, base_ref: str = "main", cwd: Optional[Path] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    run_git("worktree", "add", "-b", branch, str(path), base_ref, cwd=cwd)
