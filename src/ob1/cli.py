from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .git_ops import is_repo, current_branch, has_remote, add_worktree, GitError


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
    dry_run: bool = typer.Option(False, help="Plan actions without applying"),
):
    """Run k agents in parallel (stub for now)."""
    # Placeholder orchestration; real implementation to follow
    console.print(
        f"[bold]Would run[/bold] k={k} providers={providers} on base={base} with scope={scope} and message=\n{message}"
    )


if __name__ == "__main__":
    app()

