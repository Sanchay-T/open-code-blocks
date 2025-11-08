"""
Git worktree management for isolated agent workspaces.
"""
import subprocess
from pathlib import Path
from typing import List, Optional
import tempfile
import shutil


class WorktreeError(Exception):
    """Raised when worktree operations fail."""
    pass


class WorktreeManager:
    """
    Manages git worktrees for isolated agent workspaces.

    Each agent gets its own worktree to avoid conflicts.
    """

    def __init__(self, repo_path: str, base_branch: str = "main"):
        """
        Initialize worktree manager.

        Args:
            repo_path: Path to main git repository
            base_branch: Base branch to create worktrees from
        """
        self.repo_path = Path(repo_path).resolve()
        self.base_branch = base_branch

        if not (self.repo_path / ".git").exists():
            raise WorktreeError(f"Not a git repository: {repo_path}")

    def create(self, agent_id: str, branch_name: str) -> str:
        """
        Create a new worktree for an agent.

        Args:
            agent_id: Unique agent identifier
            branch_name: Name for the new branch

        Returns:
            str: Path to the created worktree

        Raises:
            WorktreeError: If worktree creation fails
        """
        # Create worktree in temp directory
        worktree_dir = Path(tempfile.gettempdir()) / "ob1-worktrees" / agent_id

        # Clean up if already exists
        if worktree_dir.exists():
            self.cleanup(str(worktree_dir))

        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", "origin", self.base_branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Create worktree with new branch
            subprocess.run(
                [
                    "git", "worktree", "add",
                    "-b", branch_name,
                    str(worktree_dir),
                    f"origin/{self.base_branch}"
                ],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )

            return str(worktree_dir)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)

            # Handle common errors
            if "already exists" in error_msg:
                raise WorktreeError(f"Branch {branch_name} already exists")
            elif "not a valid" in error_msg:
                raise WorktreeError(f"Invalid branch name: {branch_name}")
            else:
                raise WorktreeError(f"Failed to create worktree: {error_msg}")

    def cleanup(self, worktree_path: str) -> None:
        """
        Remove a worktree.

        Args:
            worktree_path: Path to worktree to remove
        """
        worktree_path = Path(worktree_path)

        if not worktree_path.exists():
            return

        try:
            # Remove worktree from git
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            # If git worktree remove fails, manually delete
            pass

        # Ensure directory is removed
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

    def list_worktrees(self) -> List[dict]:
        """
        List all active worktrees.

        Returns:
            List of worktree info dicts
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )

            worktrees = []
            current = {}

            for line in result.stdout.split('\n'):
                if line.startswith('worktree '):
                    if current:
                        worktrees.append(current)
                    current = {'path': line.split(' ', 1)[1]}
                elif line.startswith('branch '):
                    current['branch'] = line.split(' ', 1)[1]
                elif line.startswith('HEAD '):
                    current['head'] = line.split(' ', 1)[1]

            if current:
                worktrees.append(current)

            return worktrees

        except subprocess.CalledProcessError:
            return []

    def cleanup_all(self) -> None:
        """Remove all ob1 worktrees."""
        worktrees_base = Path(tempfile.gettempdir()) / "ob1-worktrees"
        if worktrees_base.exists():
            shutil.rmtree(worktrees_base, ignore_errors=True)

        # Prune stale worktrees in git
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            pass
