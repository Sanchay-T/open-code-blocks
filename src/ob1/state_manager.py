"""
State management for OB1 runs, PR tracking, and issue association.

This module provides persistent state tracking across OB1 runs, enabling:
- Run history and status tracking
- PR → Run → Issue association
- PR continuation (resume working on existing PRs)
- Agent performance analytics
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentRunState:
    """State for a single agent within a run."""

    name: str  # e.g., "claude-1", "cursor-2"
    provider: str  # e.g., "claude", "cursor", "codex"
    branch: str  # e.g., "ob1/20251109-143025/claude-1"
    status: str  # "pending", "running", "success", "failed"
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)  # files_changed, lines_added, etc.


@dataclass
class RunState:
    """State for an entire OB1 run (k agents working on same task)."""

    run_id: str  # timestamp-based ID: "20251109-143025"
    message: str  # task description
    target_repo: str  # target repository URL
    base_branch: str  # base branch (usually "main")
    scope_patterns: List[str]  # scope patterns like ["frontend/**"]
    issue_number: Optional[int] = None  # associated GitHub issue
    k: int = 1  # number of agents
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed"
    agents: List[AgentRunState] = field(default_factory=list)


@dataclass
class PRTrackingState:
    """Track PR continuation chain."""

    pr_number: int
    repo: str  # "owner/repo"
    branch: str
    issue_number: Optional[int] = None
    created_by_run: str  # run_id that created this PR
    continuation_runs: List[str] = field(default_factory=list)  # run_ids that continued work
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "open"  # "open", "merged", "closed"


class StateManager:
    """Manages persistent state for OB1 runs and PRs."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.state_dir = repo_root / ".ob1" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.runs_file = self.state_dir / "runs.json"
        self.pr_tracking_file = self.state_dir / "pr_tracking.json"

        # Initialize state files if they don't exist
        if not self.runs_file.exists():
            self._write_runs([])
        if not self.pr_tracking_file.exists():
            self._write_pr_tracking([])

    def _read_runs(self) -> List[RunState]:
        """Read all runs from state file."""
        try:
            data = json.loads(self.runs_file.read_text())
            return [RunState(**run) for run in data.get("runs", [])]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_runs(self, runs: List[RunState]) -> None:
        """Write runs to state file."""
        data = {"runs": [asdict(run) for run in runs]}
        self.runs_file.write_text(json.dumps(data, indent=2))

    def _read_pr_tracking(self) -> List[PRTrackingState]:
        """Read PR tracking data."""
        try:
            data = json.loads(self.pr_tracking_file.read_text())
            return [PRTrackingState(**pr) for pr in data.get("prs", [])]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_pr_tracking(self, prs: List[PRTrackingState]) -> None:
        """Write PR tracking data."""
        data = {"prs": [asdict(pr) for pr in prs]}
        self.pr_tracking_file.write_text(json.dumps(data, indent=2))

    def create_run(
        self,
        run_id: str,
        message: str,
        target_repo: str,
        base_branch: str,
        scope_patterns: List[str],
        k: int,
        issue_number: Optional[int] = None,
    ) -> RunState:
        """Create a new run state."""
        run = RunState(
            run_id=run_id,
            message=message,
            target_repo=target_repo,
            base_branch=base_branch,
            scope_patterns=scope_patterns,
            issue_number=issue_number,
            k=k,
            status="pending",
        )

        runs = self._read_runs()
        runs.append(run)
        self._write_runs(runs)
        return run

    def update_run_status(self, run_id: str, status: str) -> None:
        """Update the status of a run."""
        runs = self._read_runs()
        for run in runs:
            if run.run_id == run_id:
                run.status = status
                break
        self._write_runs(runs)

    def add_agent_to_run(
        self,
        run_id: str,
        agent_name: str,
        provider: str,
        branch: str,
    ) -> None:
        """Add an agent to a run."""
        runs = self._read_runs()
        for run in runs:
            if run.run_id == run_id:
                agent = AgentRunState(
                    name=agent_name,
                    provider=provider,
                    branch=branch,
                    status="pending",
                    started_at=datetime.utcnow().isoformat(),
                )
                run.agents.append(agent)
                break
        self._write_runs(runs)

    def update_agent_status(
        self,
        run_id: str,
        agent_name: str,
        status: str,
        pr_number: Optional[int] = None,
        pr_url: Optional[str] = None,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update agent status and PR information."""
        runs = self._read_runs()
        for run in runs:
            if run.run_id == run_id:
                for agent in run.agents:
                    if agent.name == agent_name:
                        agent.status = status
                        if pr_number:
                            agent.pr_number = pr_number
                        if pr_url:
                            agent.pr_url = pr_url
                        if error_message:
                            agent.error_message = error_message
                        if metrics:
                            agent.metrics = metrics
                        if status in ("success", "failed"):
                            agent.completed_at = datetime.utcnow().isoformat()
                        break
                break
        self._write_runs(runs)

    def get_run(self, run_id: str) -> Optional[RunState]:
        """Get a specific run by ID."""
        runs = self._read_runs()
        for run in runs:
            if run.run_id == run_id:
                return run
        return None

    def get_recent_runs(self, limit: int = 10) -> List[RunState]:
        """Get most recent runs."""
        runs = self._read_runs()
        return sorted(runs, key=lambda r: r.created_at, reverse=True)[:limit]

    def track_pr(
        self,
        pr_number: int,
        repo: str,
        branch: str,
        created_by_run: str,
        issue_number: Optional[int] = None,
    ) -> PRTrackingState:
        """Track a newly created PR."""
        pr_state = PRTrackingState(
            pr_number=pr_number,
            repo=repo,
            branch=branch,
            created_by_run=created_by_run,
            issue_number=issue_number,
            status="open",
        )

        prs = self._read_pr_tracking()
        prs.append(pr_state)
        self._write_pr_tracking(prs)
        return pr_state

    def add_pr_continuation(self, pr_number: int, run_id: str) -> None:
        """Add a continuation run to a PR."""
        prs = self._read_pr_tracking()
        for pr in prs:
            if pr.pr_number == pr_number:
                if run_id not in pr.continuation_runs:
                    pr.continuation_runs.append(run_id)
                pr.last_updated = datetime.utcnow().isoformat()
                break
        self._write_pr_tracking(prs)

    def get_pr_by_number(self, pr_number: int) -> Optional[PRTrackingState]:
        """Get PR tracking state by number."""
        prs = self._read_pr_tracking()
        for pr in prs:
            if pr.pr_number == pr_number:
                return pr
        return None

    def get_pr_by_issue(self, issue_number: int) -> Optional[PRTrackingState]:
        """Get PR associated with a GitHub issue."""
        prs = self._read_pr_tracking()
        for pr in prs:
            if pr.issue_number == issue_number:
                return pr
        return None

    def update_pr_status(self, pr_number: int, status: str) -> None:
        """Update PR status (open, merged, closed)."""
        prs = self._read_pr_tracking()
        for pr in prs:
            if pr.pr_number == pr_number:
                pr.status = status
                pr.last_updated = datetime.utcnow().isoformat()
                break
        self._write_pr_tracking(prs)

    def get_runs_for_pr(self, pr_number: int) -> List[RunState]:
        """Get all runs associated with a PR (creator + continuations)."""
        pr_state = self.get_pr_by_number(pr_number)
        if not pr_state:
            return []

        all_run_ids = [pr_state.created_by_run] + pr_state.continuation_runs
        runs = self._read_runs()
        return [run for run in runs if run.run_id in all_run_ids]

    def get_prs_for_issue(self, issue_number: int) -> List[PRTrackingState]:
        """Get all PRs associated with a GitHub issue."""
        prs = self._read_pr_tracking()
        return [pr for pr in prs if pr.issue_number == issue_number]
