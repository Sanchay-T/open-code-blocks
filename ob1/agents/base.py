"""
Base agent interface for ob1 orchestrator.

Defines the protocol that all agents must implement, allowing
for easy addition of new agent types (Claude, Codex, Cursor, etc.).
"""
from dataclasses import dataclass
from typing import Protocol, Optional, List


@dataclass
class AgentResult:
    """Result from an agent execution."""

    agent_id: str
    status: str  # "success", "failed", "timeout"
    branch_name: str
    pr_url: Optional[str] = None
    error: Optional[str] = None
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    changes_made: List[str] = None

    def __post_init__(self):
        if self.changes_made is None:
            self.changes_made = []


class Agent(Protocol):
    """
    Protocol defining the interface all agents must implement.

    This allows the orchestrator to work with any agent type
    (Claude, Codex, Cursor, etc.) without knowing implementation details.

    Example:
        class MyAgent:
            async def execute(self, task: str, workspace_path: str, branch: str) -> AgentResult:
                # Implementation here
                return AgentResult(...)
    """

    async def execute(
        self,
        task: str,
        workspace_path: str,
        branch_name: str
    ) -> AgentResult:
        """
        Execute the given task in the specified workspace.

        Args:
            task: The task description/prompt for the agent
            workspace_path: Path to the git worktree where agent should work
            branch_name: Git branch name for this agent's changes

        Returns:
            AgentResult with status, changes, and metadata

        Raises:
            AgentError: If agent execution fails
        """
        ...


class AgentError(Exception):
    """Raised when agent execution fails."""
    pass
