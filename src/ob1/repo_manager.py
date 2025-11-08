from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Optional

from .git_ops import (
    GitError,
    current_branch,
    get_origin_url,
    run_git,
)
from .github_api import RepoRef, parse_github_repo


@dataclass
class RepoContext:
    root: Path
    base_branch: str
    repo_ref: RepoRef
    is_cloned: bool


class TargetRepoManager:
    def __init__(self, base_branch: str, target_url: Optional[str] = None) -> None:
        self.base_branch = base_branch
        self.target_url = target_url
        self._root: Optional[Path] = None
        self._is_cloned = False
        self._lock = Lock()
        self._tmp_root: Optional[Path] = None

    def prepare(self) -> RepoContext:
        if self.target_url:
            self._clone_target()
        else:
            cwd = Path.cwd()
            if not (cwd / ".git").exists():
                raise GitError("Current directory is not a git repository; pass --target")
            self._root = cwd
            self._is_cloned = False

        assert self._root is not None
        origin = get_origin_url(self._root)
        owner, name = parse_github_repo(origin)
        repo_ref = RepoRef(owner=owner, name=name, origin_url=origin)

        # Ensure base branch is up to date
        run_git("fetch", "origin", self.base_branch, cwd=self._root)

        # If operating in-place ensure base branch exists locally
        if not self._is_cloned:
            current = current_branch(self._root)
            if current != self.base_branch:
                run_git("checkout", self.base_branch, cwd=self._root)

        return RepoContext(root=self._root, base_branch=self.base_branch, repo_ref=repo_ref, is_cloned=self._is_cloned)

    def cleanup(self) -> None:
        if self._is_cloned and self._tmp_root and self._tmp_root.exists():
            shutil.rmtree(self._tmp_root, ignore_errors=True)

    def _clone_target(self) -> None:
        assert self.target_url
        run_root = Path(tempfile.mkdtemp(prefix="ob1-run-"))
        target_path = run_root / "target"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        run_git("clone", "--origin", "origin", self.target_url, str(target_path))
        run_git("checkout", self.base_branch, cwd=target_path)
        self._root = target_path
        self._is_cloned = True
        self._tmp_root = run_root

    def create_worktree(self, branch: str) -> Path:
        if self._root is None:
            raise GitError("Repository not prepared")
        work_dir = self._root / ".ob1" / "worktrees" / branch.replace("/", "-")
        work_dir.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            run_git("worktree", "add", "-b", branch, str(work_dir), self.base_branch, cwd=self._root)
        return work_dir

    def remove_worktree(self, branch: str, path: Path) -> None:
        if self._root is None:
            return
        with self._lock:
            try:
                run_git("worktree", "remove", "--force", str(path), cwd=self._root)
            except GitError:
                pass
            try:
                run_git("branch", "-D", branch, cwd=self._root)
            except GitError:
                pass

    def push_branch(self, branch: str) -> None:
        if self._root is None:
            raise GitError("Repository not prepared")
        run_git("push", "-u", "origin", f"{branch}:{branch}", cwd=self._root)

