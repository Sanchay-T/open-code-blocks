from __future__ import annotations

import asyncio
import textwrap
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table

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

    settings = get_settings(config.env_file)
    _seed_process_env(settings)
    if not config.dry_run and not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN is not set; cannot create pull requests")

    repo_manager = TargetRepoManager(base_branch=config.base_branch, target_url=config.target_url)
    repo_ctx = await asyncio.to_thread(repo_manager.prepare)
    console.print(
        f"[bold]Target repo:[/bold] {repo_ctx.repo_ref.owner}/{repo_ctx.repo_ref.name} @ {repo_ctx.base_branch}"
    )

    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    agent_results: List[AgentResult] = []

    try:
        gh_client: Optional[GitHubAPI] = None
        if not config.dry_run:
            gh_client = GitHubAPI(settings.github_token)  # type: ignore[arg-type]

        provider_instances = _build_providers(config.providers, settings, console)

        tasks: List[asyncio.Task[AgentResult]] = []
        for idx in range(config.k):
            provider = config.providers[idx % len(config.providers)]
            agent_name = f"{provider}-{idx + 1}"
            branch = f"ob1/{run_id}/{agent_name}"
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
                )
            )
            tasks.append(task)

        for future in asyncio.as_completed(tasks):
            res = await future
            agent_results.append(res)
            if res.status == "success":
                status = "[green]success[/green]"
            elif res.status == "dry-run":
                status = "[yellow]dry-run[/yellow]"
            else:
                status = "[red]failed[/red]"
            msg = f"{res.agent_name} → {status}"
            if res.pr_url:
                msg += f" ({res.pr_url})"
            elif res.error:
                msg += f" — {res.error}"
            console.print(msg)

        if gh_client:
            await gh_client.close()

    finally:
        repo_manager.cleanup()

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
            if provider_result and provider_result.diff_text and provider_result.apply_diff:
                await asyncio.to_thread(apply_unified_diff, provider_result.diff_text, worktree_path)
            files = await asyncio.to_thread(list_changed_files, worktree_path)
            if not files:
                raise ChangeGuardError("Agent did not modify any files")
            await asyncio.to_thread(ensure_changes_within_scope, files, config.scope_patterns)
            await asyncio.to_thread(_commit_all, worktree_path, f"feat: {agent_name} - {config.message}")
            await asyncio.to_thread(repo_manager.push_branch, branch)
            assert gh_client is not None
            pr_title = f"{agent_name}: {config.message[:60]}"
            pr_body = textwrap.dedent(
                f"""
                Automated agent PR from `{provider_name}`.

                - Agent: `{agent_name}`
                - Task: {config.message}
                - Transcript saved locally at: {provider_result.transcript_path if provider_result else 'n/a'}
                """
            ).strip()
            pr_url = await gh_client.create_pull_request(
                repo=repo_ctx.repo_ref,
                title=pr_title,
                head=branch,
                base=repo_ctx.base_branch,
                body=pr_body,
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
    table = Table(title="Agent Run Summary", show_header=True, header_style="bold magenta")
    table.add_column("Agent")
    table.add_column("Branch")
    table.add_column("Status")
    table.add_column("PR")
    table.add_column("Error")

    for res in results:
        table.add_row(
            res.agent_name,
            res.branch,
            res.status,
            res.pr_url or "—",
            (res.error or "")[:80],
        )

    console.print(table)


def _build_providers(provider_names: List[str], settings, console: Console) -> dict[str, AgentProvider]:
    providers: dict[str, AgentProvider] = {}
    for name in set(provider_names):
        if name == "claude":
            _log_provider_secret(console, "claude", bool(getattr(settings, "claude_api_key", None)))
            providers[name] = _build_claude_provider(settings, console)
        elif name == "cursor":
            providers[name] = CursorProvider(console=console)
        elif name == "codex":
            api_key = settings.openai_api_key
            _log_provider_secret(console, "codex", bool(api_key))
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
