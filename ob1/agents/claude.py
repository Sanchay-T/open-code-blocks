"""
Claude agent implementation using the Claude Agent SDK.
"""
import asyncio
import time
from pathlib import Path
from typing import Optional

from .base import Agent, AgentResult, AgentError


class ClaudeAgent:
    """
    Agent implementation using Claude Agent SDK.

    Uses the official claude-agent-sdk to execute tasks autonomously.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5",
        max_budget_usd: float = 5.0,
        timeout: int = 600
    ):
        """
        Initialize Claude agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_budget_usd: Maximum cost budget
            timeout: Timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.max_budget_usd = max_budget_usd
        self.timeout = timeout

    async def execute(
        self,
        task: str,
        workspace_path: str,
        branch_name: str
    ) -> AgentResult:
        """
        Execute task using Claude Agent SDK.

        Args:
            task: Task description
            workspace_path: Path to git worktree
            branch_name: Branch for changes

        Returns:
            AgentResult with execution details
        """
        start_time = time.time()
        agent_id = f"claude-{branch_name}"

        try:
            # Import Claude Agent SDK
            try:
                from claude_agent_sdk import query, ClaudeAgentOptions
            except ImportError:
                raise AgentError(
                    "claude-agent-sdk not installed. "
                    "Install with: pip install claude-agent-sdk"
                )

            # Configure Claude agent
            options = ClaudeAgentOptions(
                model=self.model,
                cwd=str(Path(workspace_path).resolve()),
                allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
                permission_mode="acceptEdits",  # Auto-approve file edits
                max_budget_usd=self.max_budget_usd,
                api_key=self.api_key
            )

            # Build comprehensive prompt
            prompt = f"""
{task}

IMPORTANT INSTRUCTIONS:
1. Work in the current directory (this is a git worktree)
2. Create or modify files to complete the task
3. Make focused, high-quality changes
4. Do NOT create git commits (the orchestrator handles that)
5. Do NOT push changes (the orchestrator handles that)
6. Focus only on writing the code to complete: {task}

After making changes, summarize what you did.
"""

            changes_made = []
            cost_usd = 0.0

            # Execute with timeout
            async def run_agent():
                nonlocal changes_made, cost_usd

                async for message in query(prompt=prompt, options=options):
                    # Track file changes
                    if hasattr(message, 'type'):
                        if message.type == 'tool_call' and message.tool_name in ['Write', 'Edit']:
                            if hasattr(message, 'tool_input'):
                                file_path = message.tool_input.get('file_path', '')
                                if file_path:
                                    changes_made.append(file_path)

                        # Track cost if available
                        if message.type == 'result' and hasattr(message, 'usage'):
                            # Estimate cost (rough approximation)
                            input_tokens = getattr(message.usage, 'input_tokens', 0)
                            output_tokens = getattr(message.usage, 'output_tokens', 0)
                            # Sonnet 4.5: $3/MTok input, $15/MTok output
                            cost_usd = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

            # Run with timeout
            try:
                await asyncio.wait_for(run_agent(), timeout=self.timeout)
                status = "success"
                error = None
            except asyncio.TimeoutError:
                status = "timeout"
                error = f"Agent timed out after {self.timeout}s"

            duration = time.time() - start_time

            return AgentResult(
                agent_id=agent_id,
                status=status,
                branch_name=branch_name,
                error=error,
                cost_usd=cost_usd,
                duration_seconds=duration,
                changes_made=list(set(changes_made))  # Unique files
            )

        except Exception as e:
            duration = time.time() - start_time
            return AgentResult(
                agent_id=agent_id,
                status="failed",
                branch_name=branch_name,
                error=str(e),
                duration_seconds=duration
            )
