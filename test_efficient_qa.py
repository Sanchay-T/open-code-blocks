#!/usr/bin/env python3
"""Test the efficient QA agent"""
import asyncio
import os
from pathlib import Path
from rich.console import Console
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from ob1.efficient_qa_agent import run_efficient_qa

async def test():
    console = Console()

    github_token = os.getenv("GITHUB_TOKEN")
    claude_api_key = os.getenv("CLAUDE_API_KEY")

    if not github_token or not claude_api_key:
        console.print("[red]Set GITHUB_TOKEN and CLAUDE_API_KEY[/red]")
        return

    worktree_path = Path("/var/folders/dj/d4sqyptn3t78mw30z8vv9w0w0000gn/T/qa-test-urvqj8x7/sandbox")

    if not worktree_path.exists():
        console.print("[red]Worktree doesn't exist[/red]")
        return

    console.print("[bold cyan]⚡ Testing Efficient QA Agent[/bold cyan]\n")

    report = await run_efficient_qa(
        pr_number=28,
        repo_url="https://github.com/Sanchay-T/ob1-sandbox.git",
        worktree_path=worktree_path,
        github_token=github_token,
        claude_api_key=claude_api_key,
        console=console
    )

    console.print("\n[bold green]" + "="*60 + "[/bold green]")
    console.print("[bold green]FINAL REPORT[/bold green]")
    console.print("[bold green]" + "="*60 + "[/bold green]\n")
    console.print(report)

if __name__ == "__main__":
    asyncio.run(test())
