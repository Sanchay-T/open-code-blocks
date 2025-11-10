"""CLI commands for viewing run and PR status."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .state_manager import StateManager


def status_command(
    run_id: Optional[str] = typer.Argument(None, help="Run ID to view (default: most recent)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent runs to show"),
    pr: Optional[int] = typer.Option(None, "--pr", help="Show info for specific PR number"),
    issue: Optional[int] = typer.Option(None, "--issue", help="Show PRs for specific issue"),
) -> None:
    """View status of OB1 runs, PRs, and issues."""
    console = Console()

    # Find repo root (look for .git)
    current = Path.cwd()
    repo_root = None
    while current != current.parent:
        if (current / ".git").exists() or (current / ".ob1").exists():
            repo_root = current
            break
        current = current.parent

    if not repo_root:
        console.print("[red]Error:[/red] Not in a git repository")
        raise typer.Exit(1)

    state_mgr = StateManager(repo_root)

    if pr:
        # Show info for specific PR
        _show_pr_info(state_mgr, pr, console)
    elif issue:
        # Show PRs for specific issue
        _show_issue_prs(state_mgr, issue, console)
    elif run_id:
        # Show specific run
        _show_run_detail(state_mgr, run_id, console)
    else:
        # Show recent runs
        _show_recent_runs(state_mgr, limit, console)


def _show_recent_runs(state_mgr: StateManager, limit: int, console: Console) -> None:
    """Show table of recent runs."""
    runs = state_mgr.get_recent_runs(limit)

    if not runs:
        console.print("[yellow]No runs found[/yellow]")
        return

    table = Table(title=f"Recent {len(runs)} Runs", show_header=True, header_style="bold cyan")
    table.add_column("Run ID", style="dim")
    table.add_column("Status")
    table.add_column("Task")
    table.add_column("Agents")
    table.add_column("PRs")
    table.add_column("Issue")
    table.add_column("Created")

    for run in runs:
        # Status emoji
        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
        }.get(run.status, "❓")

        # Count successful agents
        success_count = sum(1 for a in run.agents if a.status == "success")
        failed_count = sum(1 for a in run.agents if a.status == "failed")
        agents_str = f"{success_count}✓ {failed_count}✗" if failed_count > 0 else f"{success_count}/{len(run.agents)}"

        # Count PRs
        pr_numbers = [str(a.pr_number) for a in run.agents if a.pr_number]
        prs_str = ", ".join(pr_numbers) if pr_numbers else "-"

        # Issue
        issue_str = f"#{run.issue_number}" if run.issue_number else "-"

        # Created time (just date)
        created_date = run.created_at[:10] if run.created_at else "N/A"

        table.add_row(
            run.run_id,
            f"{status_emoji} {run.status}",
            run.message[:40] + "..." if len(run.message) > 40 else run.message,
            agents_str,
            prs_str,
            issue_str,
            created_date,
        )

    console.print(table)
    console.print(f"\n[dim]Use 'ob1 status <run_id>' to view details[/dim]")


def _show_run_detail(state_mgr: StateManager, run_id: str, console: Console) -> None:
    """Show detailed information about a specific run."""
    run = state_mgr.get_run(run_id)

    if not run:
        console.print(f"[red]Run not found:[/red] {run_id}")
        raise typer.Exit(1)

    # Summary panel
    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
    }.get(run.status, "❓")

    summary = f"""
[bold]Run ID:[/bold] {run.run_id}
[bold]Status:[/bold] {status_emoji} {run.status}
[bold]Task:[/bold] {run.message}
[bold]Target:[/bold] {run.target_repo}
[bold]Base Branch:[/bold] {run.base_branch}
[bold]Scope:[/bold] {', '.join(run.scope_patterns) if run.scope_patterns else 'All files'}
[bold]Issue:[/bold] #{run.issue_number if run.issue_number else 'None'}
[bold]Agents:[/bold] {len(run.agents)} ({run.k} requested)
[bold]Created:[/bold] {run.created_at}
    """.strip()

    console.print(Panel(summary, title="Run Details", border_style="cyan"))

    # Agents table
    if run.agents:
        table = Table(title="Agents", show_header=True, header_style="bold cyan")
        table.add_column("Agent")
        table.add_column("Provider")
        table.add_column("Status")
        table.add_column("PR")
        table.add_column("Branch")
        table.add_column("Duration")
        table.add_column("Error")

        for agent in run.agents:
            status_emoji = {
                "pending": "⏳",
                "running": "🔄",
                "success": "✅",
                "failed": "❌",
            }.get(agent.status, "❓")

            pr_str = str(agent.pr_number) if agent.pr_number else "-"
            if agent.pr_url:
                pr_str = f"[link={agent.pr_url}]{pr_str}[/link]"

            # Calculate duration
            duration_str = "-"
            if agent.started_at and agent.completed_at:
                from datetime import datetime

                started = datetime.fromisoformat(agent.started_at)
                completed = datetime.fromisoformat(agent.completed_at)
                duration = (completed - started).total_seconds()
                duration_str = f"{int(duration)}s"

            error_str = (
                agent.error_message[:30] + "..." if agent.error_message and len(agent.error_message) > 30 else agent.error_message or "-"
            )

            table.add_row(
                agent.name,
                agent.provider,
                f"{status_emoji} {agent.status}",
                pr_str,
                agent.branch,
                duration_str,
                error_str,
            )

        console.print(table)


def _show_pr_info(state_mgr: StateManager, pr_number: int, console: Console) -> None:
    """Show information about a specific PR."""
    pr_state = state_mgr.get_pr_by_number(pr_number)

    if not pr_state:
        console.print(f"[red]PR not found in state:[/red] #{pr_number}")
        console.print("[dim]Note: Only PRs created by OB1 are tracked[/dim]")
        raise typer.Exit(1)

    status_emoji = {
        "open": "🟢",
        "merged": "🟣",
        "closed": "🔴",
    }.get(pr_state.status, "❓")

    summary = f"""
[bold]PR Number:[/bold] #{pr_state.pr_number}
[bold]Status:[/bold] {status_emoji} {pr_state.status}
[bold]Repository:[/bold] {pr_state.repo}
[bold]Branch:[/bold] {pr_state.branch}
[bold]Created by Run:[/bold] {pr_state.created_by_run}
[bold]Issue:[/bold] #{pr_state.issue_number if pr_state.issue_number else 'None'}
[bold]Continuations:[/bold] {len(pr_state.continuation_runs)}
[bold]Last Updated:[/bold] {pr_state.last_updated}
    """.strip()

    console.print(Panel(summary, title=f"PR #{pr_number} Details", border_style="cyan"))

    # Show all associated runs
    runs = state_mgr.get_runs_for_pr(pr_number)
    if runs:
        console.print("\n[bold]Associated Runs:[/bold]")
        for run in runs:
            console.print(f"  • {run.run_id}: {run.message[:50]}")


def _show_issue_prs(state_mgr: StateManager, issue_number: int, console: Console) -> None:
    """Show all PRs associated with an issue."""
    prs = state_mgr.get_prs_for_issue(issue_number)

    if not prs:
        console.print(f"[yellow]No PRs found for issue #{issue_number}[/yellow]")
        return

    table = Table(title=f"PRs for Issue #{issue_number}", show_header=True, header_style="bold cyan")
    table.add_column("PR")
    table.add_column("Status")
    table.add_column("Branch")
    table.add_column("Created By")
    table.add_column("Continuations")

    for pr in prs:
        status_emoji = {
            "open": "🟢",
            "merged": "🟣",
            "closed": "🔴",
        }.get(pr.status, "❓")

        table.add_row(
            f"#{pr.pr_number}",
            f"{status_emoji} {pr.status}",
            pr.branch,
            pr.created_by_run,
            str(len(pr.continuation_runs)),
        )

    console.print(table)
