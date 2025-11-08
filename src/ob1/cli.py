from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .git_ops import is_repo, current_branch, has_remote, add_worktree, GitError
from .orchestrator import RunConfig, run_orchestrator
from .claude_probe import claude_ping as claude_ping_runner
from .path_filters import parse_scope
from .qa_agent import QAReviewConfig, run_qa_review


app = typer.Typer(add_completion=False, help="OB1: run k AI agents in parallel and open PRs")
console = Console()


def _cwd() -> Path:
    return Path.cwd()


@app.command()
def doctor() -> None:
    """Quick repo diagnostics."""
    cwd = _cwd()
    tbl = Table(title="OB1 Doctor", show_header=True, header_style="bold cyan")
    tbl.add_column("Check")
    tbl.add_column("Status")

    repo_ok = is_repo(cwd)
    tbl.add_row("Git repo", "✅" if repo_ok else "❌")
    br = current_branch(cwd) if repo_ok else None
    tbl.add_row("Current branch", br or "—")
    tbl.add_row("Has origin", "✅" if (repo_ok and has_remote("origin", cwd)) else "❌")

    console.print(tbl)


@app.command()
def mkworktree(
    branch: str = typer.Argument(..., help="New branch name for the worktree"),
    base: str = typer.Option("main", help="Base ref to branch off"),
    path: Optional[Path] = typer.Option(None, help="Path to create the worktree in"),
):
    """Create a git worktree for isolated development."""
    cwd = _cwd()
    if not is_repo(cwd):
        console.print("[red]Not a git repo. Run `git init` first.[/red]")
        raise typer.Exit(1)

    wt_path = path or cwd / "worktrees" / branch.replace("/", "-")
    try:
        add_worktree(wt_path, branch=branch, base_ref=base, cwd=cwd)
    except GitError as e:
        console.print(f"[red]Failed to add worktree:[/red] {e}")
        raise typer.Exit(1)
    console.print(f"[green]Created worktree[/green] at {wt_path}")


@app.command()
def run(
    message: str = typer.Option(..., "-m", help="Task for agents, e.g. 'Build a login page'"),
    k: int = typer.Option(1, "-k", help="Number of parallel agents"),
    providers: str = typer.Option("claude", help="Comma-separated provider list"),
    base: str = typer.Option("main", help="Base ref for branches"),
    scope: Optional[str] = typer.Option(None, help="Allowed path (glob) for changes"),
    target: Optional[str] = typer.Option(None, help="Target repo URL; defaults to current repo"),
    env_file: Optional[Path] = typer.Option(None, help="Path to env file with tokens"),
    dry_run: bool = typer.Option(False, help="Plan actions without applying"),
):
    """Run k agents in parallel (initial implementation)."""
    provider_list = [p.strip() for p in providers.split(",") if p.strip()]
    if not provider_list:
        raise typer.BadParameter("At least one provider must be specified", param_hint="providers")

    scope_patterns = parse_scope(scope)

    config = RunConfig(
        message=message,
        k=k,
        providers=provider_list,
        base_branch=base,
        scope_patterns=scope_patterns,
        target_url=target,
        dry_run=dry_run,
        env_file=env_file,
    )

    try:
        asyncio.run(run_orchestrator(config, console))
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]Run failed:[/red] {exc}")
        raise typer.Exit(1) from exc


@app.command("claude-ping")
def claude_ping_command(
    prompt: str = typer.Argument(..., help="Prompt to send to Claude"),
    tools: str = typer.Option("", help="Comma-separated allowed tools (e.g. 'Read,Write,Bash')"),
    permission: str = typer.Option(
        "default", help="Permission mode: default, acceptEdits, or bypassPermissions"
    ),
    cwd: Optional[Path] = typer.Option(None, help="Working directory for Claude (defaults to repo root)"),
    system_prompt: Optional[str] = typer.Option(None, help="Optional system prompt override"),
    env_file: Optional[Path] = typer.Option(None, help="Custom .env file with CLAUDE_API_KEY"),
):
    """Send a one-off prompt to Claude Agent SDK and stream the raw transcript."""
    allowed_tools = [tool.strip() for tool in tools.split(",") if tool.strip()]
    try:
        claude_ping_runner(
            prompt=prompt,
            allowed_tools=allowed_tools,
            permission_mode=permission,
            cwd=cwd,
            system_prompt=system_prompt,
            env_file=env_file,
            console=console,
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise typer.Exit(1) from exc

@app.command()
def qa(
    pr: int = typer.Option(..., "--pr", help="Pull request number to review"),
    target: Optional[str] = typer.Option(None, help="Target repo URL; defaults to current repo"),
    build_log: Optional[Path] = typer.Option(None, help="Path to build log output"),
    test_log: Optional[Path] = typer.Option(None, help="Path to Playwright log output"),
    artifacts: str = typer.Option(
        "Playwright report, Playwright videos", help="Comma-separated artifact names to mention"
    ),
    env_file: Optional[Path] = typer.Option(None, help="Custom env file with tokens"),
    dry_run: bool = typer.Option(False, help="Print review instead of posting"),
):
    """Run the Stage 2 QA Testing Agent on a PR."""
    config = QAReviewConfig(
        pr_number=pr,
        repo_url=target,
        build_log=build_log,
        test_log=test_log,
        artifact_note=artifacts,
        env_file=env_file,
        dry_run=dry_run,
    )
    try:
        run_qa_review(config, console)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]QA failed:[/red] {exc}")
        raise typer.Exit(1) from exc


if __name__ == "__main__":
    app()
