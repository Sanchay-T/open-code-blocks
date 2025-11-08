"""
CLI entry point for ob1 orchestrator.
"""
import asyncio
import click
from pathlib import Path
from rich.console import Console

from .utils.config import Config, ConfigError
from .orchestrator import Orchestrator


console = Console()


@click.command()
@click.option(
    '-m', '--message',
    required=True,
    help='Task message for agents (e.g., "Build a login page")'
)
@click.option(
    '-k', '--agents',
    default=3,
    type=int,
    help='Number of parallel agents to run (default: 3)'
)
@click.option(
    '--repo',
    default='.',
    type=click.Path(exists=True),
    help='Path to git repository (default: current directory)'
)
@click.option(
    '--model',
    default=None,
    help='Claude model to use (default: from config or claude-sonnet-4-5)'
)
def main(message: str, agents: int, repo: str, model: str):
    """
    ob1 - Parallel AI SWE Agent Orchestrator

    Runs multiple AI agents in parallel on the same task, each creating a pull request.

    Example:
        ob1 -m "Build a React login component" -k 3
    """
    try:
        # Load configuration
        try:
            config = Config.load()
        except ConfigError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            console.print("\n[yellow]Required environment variables:[/yellow]")
            console.print("  - GITHUB_TOKEN")
            console.print("  - ANTHROPIC_API_KEY")
            raise click.Abort()

        # Override model if specified
        if model:
            config.default_model = model

        # Validate inputs
        if agents < 1:
            console.print("[red]Error: Number of agents must be at least 1[/red]")
            raise click.Abort()

        if agents > config.max_parallel:
            console.print(
                f"[yellow]Warning: Requested {agents} agents, "
                f"but max_parallel is {config.max_parallel}. "
                f"Using {config.max_parallel}.[/yellow]"
            )
            agents = config.max_parallel

        # Verify repo is a git repository
        repo_path = Path(repo).resolve()
        if not (repo_path / ".git").exists():
            console.print(f"[red]Error: {repo_path} is not a git repository[/red]")
            raise click.Abort()

        # Display configuration
        console.print("\n[bold cyan]Configuration:[/bold cyan]")
        console.print(f"  Task: {message}")
        console.print(f"  Agents: {agents}")
        console.print(f"  Model: {config.default_model}")
        console.print(f"  Repository: {repo_path}")
        console.print()

        # Create orchestrator
        orchestrator = Orchestrator(config, str(repo_path))

        # Run agents
        results = asyncio.run(orchestrator.run(message, agents))

        # Exit code based on results
        successful = sum(1 for r in results if r.status == "success" and r.pr_url)
        if successful == 0:
            console.print("[red]All agents failed[/red]")
            raise click.Abort()
        elif successful < agents:
            console.print(f"[yellow]Partial success: {successful}/{agents} agents succeeded[/yellow]")
        else:
            console.print(f"[green]✓ Success: All {agents} agents completed![/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
