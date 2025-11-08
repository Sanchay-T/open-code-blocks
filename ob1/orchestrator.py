"""
Main orchestrator for running parallel AI agents.
"""
import asyncio
from pathlib import Path
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .agents.base import AgentResult
from .agents.claude import ClaudeAgent
from .workspace.worktree import WorktreeManager, WorktreeError
from .workspace.github_pr import GitHubPRCreator, GitHubPRError
from .utils.config import Config


console = Console()


class Orchestrator:
    """
    Orchestrates multiple AI agents working in parallel.

    Each agent gets its own git worktree and creates a pull request.
    """

    def __init__(self, config: Config, repo_path: str):
        """
        Initialize orchestrator.

        Args:
            config: Application configuration
            repo_path: Path to git repository
        """
        self.config = config
        self.repo_path = Path(repo_path).resolve()

        # Initialize managers
        self.worktree_manager = WorktreeManager(str(self.repo_path))

        # Extract repo URL for GitHub
        self.repo_url = self._get_repo_url()
        self.pr_creator = GitHubPRCreator(config.github_token, self.repo_url)

    def _get_repo_url(self) -> str:
        """Extract GitHub repo URL from git config."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise ValueError("Could not determine repository URL from git config")

    async def run(self, task: str, k: int = 3) -> List[AgentResult]:
        """
        Run k agents in parallel on the same task.

        Args:
            task: Task description for agents
            k: Number of agents to run in parallel

        Returns:
            List of AgentResult from each agent
        """
        console.print(f"\n🚀 [bold blue]ob1 orchestrator starting with {k} agents[/bold blue]\n")

        # Create agents
        agents = [
            ClaudeAgent(
                api_key=self.config.anthropic_api_key,
                model=self.config.default_model,
                timeout=self.config.timeout
            )
            for _ in range(k)
        ]

        # Run agents in parallel with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:

            # Create progress tasks
            progress_tasks = [
                progress.add_task(f"[cyan]Agent {i+1}", total=None)
                for i in range(k)
            ]

            # Run agents
            results = await asyncio.gather(
                *[
                    self._run_single_agent(
                        agent_id=f"agent-{i+1}",
                        agent=agents[i],
                        task=task,
                        progress=progress,
                        progress_task_id=progress_tasks[i]
                    )
                    for i in range(k)
                ],
                return_exceptions=True
            )

        # Filter out exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                console.print(f"[red]✗ Agent {i+1} crashed: {result}[/red]")
                # Create error result
                from .agents.base import AgentResult
                final_results.append(AgentResult(
                    agent_id=f"agent-{i+1}",
                    status="failed",
                    branch_name=f"ob1-agent-{i+1}",
                    error=str(result)
                ))
            else:
                final_results.append(result)

        # Print summary
        self._print_summary(final_results)

        return final_results

    async def _run_single_agent(
        self,
        agent_id: str,
        agent: ClaudeAgent,
        task: str,
        progress: Progress,
        progress_task_id: int
    ) -> AgentResult:
        """
        Run a single agent through the full workflow.

        Workflow:
        1. Create git worktree
        2. Run agent to make changes
        3. Create pull request
        4. Cleanup worktree
        """
        branch_name = f"ob1-{agent_id}"
        worktree_path = None

        try:
            # Step 1: Create worktree
            progress.update(progress_task_id, description=f"[cyan]{agent_id}: Creating worktree")
            worktree_path = self.worktree_manager.create(agent_id, branch_name)

            # Step 2: Run agent
            progress.update(progress_task_id, description=f"[yellow]{agent_id}: Running Claude")
            result = await agent.execute(task, worktree_path, branch_name)

            if result.status != "success":
                progress.update(progress_task_id, description=f"[red]{agent_id}: Failed")
                return result

            # Step 3: Create PR
            progress.update(progress_task_id, description=f"[green]{agent_id}: Creating PR")

            pr_title = f"[ob1] {task[:60]}"
            pr_body = f"""## Task
{task}

## Agent
- **ID**: {agent_id}
- **Model**: {self.config.default_model}
- **Duration**: {result.duration_seconds:.1f}s
- **Cost**: ${result.cost_usd:.4f}

## Changes
{len(result.changes_made)} file(s) modified

## Files Changed
{chr(10).join(f'- {f}' for f in result.changes_made[:20])}

---
🤖 Generated by [ob1](https://github.com/anthropics/open-code-blocks)
"""

            try:
                pr_url = self.pr_creator.create_pr(
                    worktree_path=worktree_path,
                    branch_name=branch_name,
                    title=pr_title,
                    body=pr_body
                )
                result.pr_url = pr_url
                progress.update(progress_task_id, description=f"[bold green]✓ {agent_id}: PR created")
            except GitHubPRError as e:
                result.status = "failed"
                result.error = f"PR creation failed: {e}"
                progress.update(progress_task_id, description=f"[red]✗ {agent_id}: PR failed")

            return result

        except WorktreeError as e:
            progress.update(progress_task_id, description=f"[red]✗ {agent_id}: Worktree error")
            from .agents.base import AgentResult
            return AgentResult(
                agent_id=agent_id,
                status="failed",
                branch_name=branch_name,
                error=f"Worktree error: {e}"
            )

        except Exception as e:
            progress.update(progress_task_id, description=f"[red]✗ {agent_id}: Error")
            from .agents.base import AgentResult
            return AgentResult(
                agent_id=agent_id,
                status="failed",
                branch_name=branch_name,
                error=str(e)
            )

        finally:
            # Cleanup worktree
            if worktree_path:
                try:
                    self.worktree_manager.cleanup(worktree_path)
                except:
                    pass

    def _print_summary(self, results: List[AgentResult]) -> None:
        """Print execution summary."""
        console.print("\n" + "=" * 70)
        console.print("[bold]Results Summary[/bold]\n")

        successful = [r for r in results if r.status == "success" and r.pr_url]
        failed = [r for r in results if r.status != "success" or not r.pr_url]

        console.print(f"Total agents: {len(results)}")
        console.print(f"[green]✓ Successful: {len(successful)}[/green]")
        console.print(f"[red]✗ Failed: {len(failed)}[/red]")

        total_cost = sum(r.cost_usd for r in results)
        total_time = max(r.duration_seconds for r in results) if results else 0

        console.print(f"\n💰 Total cost: ${total_cost:.4f}")
        console.print(f"⏱️  Total time: {total_time:.1f}s")

        console.print("\n[bold]Pull Requests Created:[/bold]\n")
        for result in successful:
            console.print(
                f"  [green]✓[/green] {result.agent_id}: {result.pr_url} "
                f"({result.duration_seconds:.1f}s, ${result.cost_usd:.4f})"
            )

        if failed:
            console.print("\n[bold]Failed Agents:[/bold]\n")
            for result in failed:
                console.print(f"  [red]✗[/red] {result.agent_id}: {result.error}")

        console.print("=" * 70 + "\n")
