"""Cinematic animations for key moments."""

from rich.console import Console
from rich.panel import Panel
from rich_gradient import Gradient


OB1_LOGO = """
   ▒█████   ▄▄▄▄    ░░███
  ▒██▒  ██▒▓█████▄ ░░░███
  ▒██░  ██▒▒██▒ ▄██  ░███
  ▒██   ██░▒██░█▀   ░░███
  ░ ████▓▒░░▓█  ▀█▓  ░███
  ░ ▒░▒░▒░ ░▒▓███▀▒  ░░░
    ░ ▒ ▒░ ▒░▒   ░
  ░ ░ ░ ▒   ░    ░
      ░ ░   ░
              AI Agent Orchestrator
"""


def show_splash(console: Console) -> None:
    """Show animated splash screen on startup."""
    # Simplified splash (terminaltexteffects can be slow)
    # Use gradient for impact instead
    logo_gradient = Gradient(
        OB1_LOGO,
        colors=["cyan", "blue", "magenta"],
        rainbow=False
    )

    console.print()
    console.print(Panel(
        logo_gradient,
        border_style="bold cyan",
        padding=(1, 2)
    ))
    console.print()


def celebrate_success(console: Console, pr_count: int, total_time: str, total_cost: float = 0.0) -> None:
    """Show celebration when all agents succeed."""
    message_lines = [
        "",
        "[bold green]✨ SUCCESS! ✨[/bold green]",
        "",
        f"[cyan]{pr_count} Pull Request{'s' if pr_count != 1 else ''} Created[/cyan]",
        f"[dim]Completed in {total_time}[/dim]",
    ]

    if total_cost > 0:
        message_lines.append(f"[dim]Estimated cost: ${total_cost:.3f}[/dim]")

    message_lines.extend([
        "",
        "[yellow]Ready for review![/yellow]",
        ""
    ])

    message = "\n".join(message_lines)

    # Create gradient panel
    console.print()
    console.print(Panel(
        message,
        border_style="bold green",
        padding=(1, 2),
        title="[bold]🎉 Agent Run Complete[/bold]",
        title_align="center"
    ))
    console.print()


def show_error_summary(console: Console, failed_agents: list, total_time: str) -> None:
    """Show error summary when agents fail."""
    message_lines = [
        "",
        "[bold red]⚠️  SOME AGENTS FAILED[/bold red]",
        "",
        f"[red]{len(failed_agents)} agent(s) encountered errors[/red]",
        f"[dim]Total runtime: {total_time}[/dim]",
        "",
    ]

    for agent in failed_agents:
        message_lines.append(f"[red]✗[/red] {agent['name']}: {agent['error'][:60]}...")

    message_lines.extend([
        "",
        "[yellow]Check transcripts for details[/yellow]",
        ""
    ])

    message = "\n".join(message_lines)

    console.print()
    console.print(Panel(
        message,
        border_style="bold red",
        padding=(1, 2),
        title="[bold]❌ Run Summary[/bold]",
        title_align="center"
    ))
    console.print()
