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
            # Import Anthropic SDK
            try:
                from anthropic import Anthropic
            except ImportError:
                raise AgentError(
                    "anthropic not installed. "
                    "Install with: pip install anthropic"
                )

            # Initialize Anthropic client
            client = Anthropic(api_key=self.api_key)

            # Build comprehensive prompt
            system_prompt = """You are an expert software engineer. You will be given a task to complete.
Write the code files needed to complete the task. Be concise and focused.
List the files you created/modified at the end."""

            user_prompt = f"""Task: {task}

Working directory: {workspace_path}

IMPORTANT:
1. Create or modify files to complete this task
2. Write clean, working code
3. List all files you created/modified

Complete this task now."""

            changes_made = []
            cost_usd = 0.0

            # Execute with timeout
            async def run_agent():
                nonlocal changes_made, cost_usd

                # Call Claude API
                response = client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                # Extract response
                response_text = response.content[0].text

                # Calculate cost
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost_usd = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

                # Parse response and create a simple file
                # For MVP, create a basic implementation file
                impl_file = Path(workspace_path) / "implementation.md"
                impl_file.write_text(f"# Task: {task}\n\n## Implementation\n\n{response_text}")
                changes_made.append(str(impl_file))

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
