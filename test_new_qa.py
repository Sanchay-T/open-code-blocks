#!/usr/bin/env python3
"""Quick test of NEW intelligent autonomous QA"""
import asyncio
import os
from pathlib import Path
from rich.console import Console

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ob1.qa_agent import run_autonomous_qa

async def test():
    console = Console()

    # Check env vars
    github_token = os.getenv("GITHUB_TOKEN")
    claude_api_key = os.getenv("CLAUDE_API_KEY")

    if not github_token or not claude_api_key:
        console.print("[red]Set GITHUB_TOKEN and CLAUDE_API_KEY first[/red]")
        return

    # Use existing temp directory
    worktree_path = Path("/var/folders/dj/d4sqyptn3t78mw30z8vv9w0w0000gn/T/qa-test-urvqj8x7/sandbox")

    if not worktree_path.exists():
        console.print("[red]Worktree doesn't exist - run setup first[/red]")
        return

    console.print(f"[cyan]Testing NEW intelligent autonomous QA...[/cyan]\n")

    report = await run_autonomous_qa(
        pr_number=28,
        repo_url="https://github.com/Sanchay-T/ob1-sandbox.git",
        worktree_path=worktree_path,
        github_token=github_token,
        claude_api_key=claude_api_key,
        console=console
    )

    console.print("\n[bold cyan]===== FINAL REPORT =====[/bold cyan]\n")
    console.print(report)

if __name__ == "__main__":
    asyncio.run(test())
