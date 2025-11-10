from __future__ import annotations

import asyncio
import textwrap
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.live import Live

from .change_guard import ChangeGuardError, ensure_changes_within_scope, list_changed_files
from .context_engine import RepoContext as RepoPromptContext, build_prompt_text, gather_repo_context
from .github_api import GitHubAPI
from .path_filters import parse_scope
from .providers.base import AgentProvider, ProviderResult
from .providers.claude import ClaudeProvider
from .providers.codex import CodexProvider
from .providers.cursor import CursorProvider
from .repo_manager import RepoContext, TargetRepoManager
from .settings import get_settings
from .git_ops import GitError, run_git
from .diff_utils import apply_unified_diff
from .state_manager import StateManager
from .ui import LiveDashboard, show_splash, celebrate_success, show_error_summary
from .utils.timer import AgentTimer


@dataclass
class RunConfig:
    message: str
    k: int
    providers: List[str]
    base_branch: str
    scope_patterns: List[str]
    target_url: Optional[str]
    dry_run: bool
    env_file: Optional[Path]
    issue_number: Optional[int] = None  # GitHub issue to associate with PRs
    continue_pr: Optional[int] = None  # PR number to continue working on


@dataclass
class AgentResult:
    agent_name: str
    branch: str
    status: str
    pr_url: Optional[str] = None
    error: Optional[str] = None
    transcript_path: Optional[Path] = None


async def run_orchestrator(config: RunConfig, console: Console) -> None:
    if config.k < 1:
        raise ValueError("k must be >= 1")

    # Show splash screen
    show_splash(console)

    settings = get_settings(config.env_file)
    _seed_process_env(settings)
    if not config.dry_run and not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN is not set; cannot create pull requests")

    # Setup with spinner
    repo_manager = TargetRepoManager(base_branch=config.base_branch, target_url=config.target_url)
    with console.status("[bold cyan]Initializing orchestrator...", spinner="dots"):
        repo_ctx = await asyncio.to_thread(repo_manager.prepare)

    console.print(
        f"[bold cyan]Target repo:[/bold cyan] {repo_ctx.repo_ref.owner}/{repo_ctx.repo_ref.name} @ {repo_ctx.base_branch}"
    )

    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    start_time = time.time()
    agent_results: List[AgentResult] = []

    # Initialize state manager
    state_mgr = StateManager(repo_ctx.root)

    # Create run state
    state_mgr.create_run(
        run_id=run_id,
        message=config.message,
        target_repo=f"{repo_ctx.repo_ref.owner}/{repo_ctx.repo_ref.name}",
        base_branch=config.base_branch,
        scope_patterns=config.scope_patterns,
        k=config.k,
        issue_number=config.issue_number,
    )
    state_mgr.update_run_status(run_id, "running")

    # Create agent names and providers for dashboard
    agent_names = []
    provider_list = []
    for idx in range(config.k):
        provider = config.providers[idx % len(config.providers)]
        agent_name = f"{provider}-{idx + 1}"
        agent_names.append(agent_name)
        provider_list.append(provider)

    # Create live dashboard
    dashboard = LiveDashboard(agent_names, provider_list, config.message, console)

    try:
        gh_client: Optional[GitHubAPI] = None
        if not config.dry_run:
            gh_client = GitHubAPI(settings.github_token)  # type: ignore[arg-type]

        with console.status(f"[bold cyan]Preparing {len(set(config.providers))} provider(s)...", spinner="dots"):
            provider_instances = _build_providers(config.providers, settings, console)

        # Initialize all agents in dashboard as pending
        for agent_name in agent_names:
            dashboard.update_agent(agent_name, status='pending', activity='Waiting to start...')

        # Start live display
        with Live(dashboard.render(), console=console, refresh_per_second=4, transient=False) as live:
            tasks: List[asyncio.Task[AgentResult]] = []
            for idx in range(config.k):
                provider = config.providers[idx % len(config.providers)]
                agent_name = f"{provider}-{idx + 1}"
                branch = f"ob1/{run_id}/{agent_name}"

                # Add agent to state
                state_mgr.add_agent_to_run(run_id, agent_name, provider, branch)

                # Mark as running in dashboard
                dashboard.update_agent(agent_name, status='running', activity='Starting...')
                live.update(dashboard.render())

                task = asyncio.create_task(
                    _run_single_agent(
                        agent_name=agent_name,
                        branch=branch,
                        provider_name=provider,
                        provider=provider_instances[provider],
                        config=config,
                        repo_ctx=repo_ctx,
                        repo_manager=repo_manager,
                        gh_client=gh_client,
                        state_mgr=state_mgr,
                        run_id=run_id,
                    )
                )
                tasks.append((agent_name, task))

            # Process results as they complete
            pending_tasks = [task for _, task in tasks]
            task_map = {task: agent_name for agent_name, task in tasks}

            while pending_tasks:
                done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)

                for completed_task in done:
                    agent_name = task_map[completed_task]
                    res = await completed_task
                    agent_results.append(res)

                    # Update dashboard with result
                    if res.status == "success":
                        dashboard.update_agent(
                            agent_name,
                            status='success',
                            activity='PR created successfully!',
                            pr_url=res.pr_url
                        )
                    elif res.status == "dry-run":
                        dashboard.update_agent(
                            agent_name,
                            status='dry-run',
                            activity='Dry-run completed (no changes made)'
                        )
                    else:
                        dashboard.update_agent(
                            agent_name,
                            status='failed',
                            error=res.error or 'Unknown error'
                        )

                    live.update(dashboard.render())

                pending_tasks = list(pending_tasks)

        if gh_client:
            await gh_client.close()

    finally:
        repo_manager.cleanup()

    # Calculate total time
    total_time = time.time() - start_time
    mins = int(total_time // 60)
    secs = int(total_time % 60)
    time_str = f"{mins:02d}:{secs:02d}"

    # Show celebration or error summary
    success_count = dashboard.get_success_count()
    if success_count == len(agent_names):
        celebrate_success(console, success_count, time_str)
    elif dashboard.get_failed_agents():
        show_error_summary(console, dashboard.get_failed_agents(), time_str)

    _render_summary(agent_results, console)


async def _run_single_agent(
    agent_name: str,
    branch: str,
    provider_name: str,
    provider: AgentProvider,
    config: RunConfig,
    repo_ctx: RepoContext,
    repo_manager: TargetRepoManager,
    gh_client: Optional[GitHubAPI],
    state_mgr: StateManager,
    run_id: str,
) -> AgentResult:
    worktree_path: Optional[Path] = None
    try:
        worktree_path = await asyncio.to_thread(repo_manager.create_worktree, branch)

        prompt_context = await asyncio.to_thread(
            gather_repo_context,
            worktree_path,
            config.scope_patterns,
        )
        prompt_text = build_prompt_text(config.message, config.scope_patterns, prompt_context)
        provider_result: Optional[ProviderResult] = None
        if config.dry_run:
            status = "dry-run"
            pr_url = None
        else:
            provider_result = await provider.run(
                agent_name=agent_name,
                branch=branch,
                prompt=prompt_text,
                worktree=worktree_path,
                repo_root=repo_ctx.root,
                scope_patterns=config.scope_patterns,
            )
            if provider_result and provider_result.diff_text:
                await asyncio.to_thread(apply_unified_diff, provider_result.diff_text, worktree_path)
            files = await asyncio.to_thread(list_changed_files, worktree_path)
            if not files:
                raise ChangeGuardError("Agent did not modify any files")
            await asyncio.to_thread(ensure_changes_within_scope, files, config.scope_patterns)
            await asyncio.to_thread(_commit_all, worktree_path, f"feat: {agent_name} - {config.message}")
            await asyncio.to_thread(repo_manager.push_branch, branch)
            assert gh_client is not None
            pr_title = f"{agent_name}: {config.message[:60]}"

            # Build PR body with issue association
            issue_reference = f"\n\nCloses #{config.issue_number}" if config.issue_number else ""
            pr_body = textwrap.dedent(
                f"""
                Automated agent PR from `{provider_name}`.

                - Agent: `{agent_name}`
                - Run ID: `{run_id}`
                - Task: {config.message}
                - Transcript saved locally at: {provider_result.transcript_path if provider_result else 'n/a'}
                {issue_reference}
                """
            ).strip()

            pr_url = await gh_client.create_pull_request(
                repo=repo_ctx.repo_ref,
                title=pr_title,
                head=branch,
                base=repo_ctx.base_branch,
                body=pr_body,
            )

            # Extract PR number from URL (format: https://github.com/owner/repo/pull/123)
            pr_number = int(pr_url.split("/")[-1]) if pr_url else None

            # Track PR in state
            if pr_number:
                state_mgr.track_pr(
                    pr_number=pr_number,
                    repo=f"{repo_ctx.repo_ref.owner}/{repo_ctx.repo_ref.name}",
                    branch=branch,
                    created_by_run=run_id,
                    issue_number=config.issue_number,
                )
                # Update agent state with PR info
                state_mgr.update_agent_status(
                    run_id=run_id,
                    agent_name=agent_name,
                    status="success",
                    pr_number=pr_number,
                    pr_url=pr_url,
                )

            status = "success"

        return AgentResult(
            agent_name=agent_name,
            branch=branch,
            status=status,
            pr_url=pr_url,
            transcript_path=provider_result.transcript_path if provider_result else None,
        )

    except Exception as exc:  # pylint: disable=broad-except
        # Update agent state with failure
        state_mgr.update_agent_status(
            run_id=run_id,
            agent_name=agent_name,
            status="failed",
            error_message=str(exc),
        )
        return AgentResult(agent_name=agent_name, branch=branch, status="failed", error=str(exc))
    finally:
        if worktree_path is not None:
            await asyncio.to_thread(repo_manager.remove_worktree, branch, worktree_path)


def _commit_all(worktree: Path, message: str) -> None:
    run_git("add", "-A", cwd=worktree)
    try:
        run_git("commit", "-m", message, cwd=worktree)
    except GitError as err:
        # No changes to commit
        if "nothing to commit" not in str(err):
            raise


def _render_summary(results: List[AgentResult], console: Console) -> None:
    """Render beautiful summary table with emojis and colors."""
    from rich.panel import Panel
    from rich_gradient import Gradient

    # Header with gradient
    header = Gradient(
        "🎉 Agent Run Complete!",
        colors=["cyan", "magenta", "yellow"]
    )
    console.print(Panel(header, border_style="bold cyan", padding=(0, 1)))
    console.print()  # Blank line

    # Enhanced table
    table = Table(
        title="Agent Results",
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        show_lines=False,
    )
    table.add_column("Agent", style="bold")
    table.add_column("Branch", style="dim")
    table.add_column("Status")
    table.add_column("PR")
    table.add_column("Error", style="red")

    # Status emojis
    status_map = {
        "success": "[green]✓ success[/green]",
        "failed": "[red]✗ failed[/red]",
        "dry-run": "[yellow]🔍 dry-run[/yellow]",
    }

    for res in results:
        # Add emoji to agent name based on provider
        agent_emoji = "🟣" if "claude" in res.agent_name else "🔵" if "cursor" in res.agent_name else "🟢"
        agent_display = f"{agent_emoji} {res.agent_name}"

        # Format PR URL as clickable link (terminals with OSC 8 support)
        pr_display = "—"
        if res.pr_url:
            # Extract PR number from URL
            pr_num = res.pr_url.split("/")[-1]
            pr_display = f"[link={res.pr_url}]PR #{pr_num}[/link]"

        table.add_row(
            agent_display,
            res.branch.split("/")[-1],  # Show only last part of branch
            status_map.get(res.status, res.status),
            pr_display,
            (res.error or "")[:80],
        )

    console.print(table)


def _build_providers(provider_names: List[str], settings, console: Console) -> dict[str, AgentProvider]:
    providers: dict[str, AgentProvider] = {}
    for name in set(provider_names):
        if name == "claude":
            # Remove noisy credential logging - credentials are validated elsewhere
            providers[name] = _build_claude_provider(settings, console)
        elif name == "cursor":
            providers[name] = CursorProvider(console=console)
        elif name == "codex":
            api_key = settings.openai_api_key
            # Remove noisy credential logging
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY (or CODEX_CLI_KEY) is required for provider 'codex'")
            providers[name] = CodexProvider(api_key=api_key, console=console)
        else:
            raise RuntimeError(f"Unsupported provider '{name}'")
    return providers


def _build_claude_provider(settings, console: Console) -> ClaudeProvider:
    api_key = settings.claude_api_key
    if not api_key:
        raise RuntimeError("CLAUDE_API_KEY is required for Claude-based providers")
    return ClaudeProvider(
        api_key=api_key,
        console=console,
        allowed_tools=[
            "Task",
            "Read",
            "Write",
            "Edit",
            "NotebookEdit",
            "Glob",
            "Grep",
            "Bash",
            "BashOutput",
        ],
    )


def _seed_process_env(settings) -> None:
    env_mapping = {
        "CLAUDE_API_KEY": getattr(settings, "claude_api_key", None),
        "ANTHROPIC_API_KEY": getattr(settings, "claude_api_key", None),
        "OPENAI_API_KEY": getattr(settings, "openai_api_key", None),
        "CURSOR_API_KEY": getattr(settings, "cursor_api_key", None),
    }
    for key, value in env_mapping.items():
        if value and not os.environ.get(key):
            os.environ[key] = value

def _log_provider_secret(console: Console, provider_name: str, present: bool) -> None:
    status = "present" if present else "missing"
    console.log(f"[provider-init] {provider_name} credential {status}")
