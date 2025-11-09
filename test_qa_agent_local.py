#!/usr/bin/env python3
"""
Local testing script for autonomous QA agent
Run this BEFORE deploying to verify QA agent works correctly

Usage:
    python test_qa_agent_local.py

This script will:
1. Clone the sandbox repo to a temp worktree
2. Run the autonomous QA agent against an existing PR
3. Verify it generates feature-specific tests (not hardcoded login)
4. Verify the test runs and records video
5. Report success/failure
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ob1.qa_agent import run_autonomous_qa
from rich.console import Console


async def test_autonomous_qa_agent():
    """Test the autonomous QA agent locally"""
    console = Console()

    console.print("\n[bold cyan]🧪 Testing Autonomous QA Agent[/bold cyan]\n")

    # Configuration
    PR_NUMBER = 28  # Use existing PR with dashboard changes
    REPO_URL = "https://github.com/Sanchay-T/ob1-sandbox.git"

    # Check environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    claude_api_key = os.getenv("CLAUDE_API_KEY")

    if not github_token:
        console.print("[red]❌ GITHUB_TOKEN not set[/red]")
        console.print("Set it with: export GITHUB_TOKEN=your_token")
        return False

    if not claude_api_key:
        console.print("[red]❌ CLAUDE_API_KEY not set[/red]")
        console.print("Set it with: export CLAUDE_API_KEY=your_key")
        return False

    # Create temporary worktree
    temp_dir = Path(tempfile.mkdtemp(prefix="qa-test-"))
    worktree_path = temp_dir / "sandbox"

    console.print(f"[dim]Creating test worktree in {temp_dir}[/dim]")

    try:
        # Clone repo
        console.print(f"[dim]Cloning {REPO_URL}...[/dim]")
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(worktree_path)],
            check=True,
            capture_output=True
        )

        # Install frontend dependencies
        console.print("[dim]Installing frontend dependencies...[/dim]")
        frontend_dir = worktree_path / "frontend"

        subprocess.run(
            ["npm", "install"],
            cwd=str(frontend_dir),
            check=True,
            capture_output=True
        )

        # Install Playwright browsers
        console.print("[dim]Installing Playwright browsers...[/dim]")
        subprocess.run(
            ["npx", "playwright", "install", "--with-deps"],
            cwd=str(frontend_dir),
            check=True,
            capture_output=True
        )

        # Build the frontend
        console.print("[dim]Building frontend...[/dim]")
        build_result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True
        )

        # Write build log
        (worktree_path / "build.log").write_text(build_result.stdout + build_result.stderr)

        # Start preview server in background
        console.print("[dim]Starting preview server...[/dim]")
        preview_proc = subprocess.Popen(
            ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to be ready
        await asyncio.sleep(5)

        # Set base URL for Playwright
        os.environ["PLAYWRIGHT_BASE_URL"] = "http://127.0.0.1:4173"

        console.print(f"\n[bold]Testing QA Agent against PR #{PR_NUMBER}[/bold]\n")

        # Run autonomous QA agent
        report = await run_autonomous_qa(
            pr_number=PR_NUMBER,
            repo_url=REPO_URL,
            worktree_path=worktree_path,
            github_token=github_token,
            claude_api_key=claude_api_key,
            console=console
        )

        # Verify results
        console.print("\n[bold cyan]📋 Generated Report:[/bold cyan]\n")
        console.print(report)
        console.print()

        # Verification checks
        console.print("[bold cyan]🔍 Verification Checks:[/bold cyan]\n")

        checks_passed = 0
        total_checks = 6

        # Check 1: Test file was created
        test_dir = worktree_path / "frontend" / "tests" / "qa"
        test_files = list(test_dir.glob("pr-*.spec.ts"))

        if test_files:
            console.print(f"[green]✓[/green] Test file created: {test_files[0].name}")
            checks_passed += 1
        else:
            console.print("[red]✗[/red] No test file created")

        # Check 2: Test is feature-specific (not hardcoded login)
        if test_files:
            test_content = test_files[0].read_text()
            # PR #28 is about dashboard, so test should NOT mention login
            if "dashboard" in test_content.lower() or "metrics" in test_content.lower():
                console.print(f"[green]✓[/green] Test is feature-specific (found dashboard/metrics)")
                checks_passed += 1
            elif "login" in test_content.lower() and "dashboard" not in test_content.lower():
                console.print(f"[red]✗[/red] Test appears hardcoded to login (should test dashboard)")
            else:
                console.print(f"[yellow]⚠[/yellow] Test content unclear")
                checks_passed += 0.5

        # Check 3: Report mentions the actual feature (dashboard)
        if "dashboard" in report.lower() or "metrics" in report.lower():
            console.print(f"[green]✓[/green] Report mentions dashboard/metrics")
            checks_passed += 1
        else:
            console.print(f"[red]✗[/red] Report doesn't mention dashboard")

        # Check 4: Report is not hardcoded (no hardcoded login text)
        if "fill the login form" in report.lower() or "fill login form" in report.lower():
            console.print(f"[red]✗[/red] Report contains hardcoded login text")
        else:
            console.print(f"[green]✓[/green] No hardcoded login text in report")
            checks_passed += 1

        # Check 5: Video was recorded
        video_dir = frontend_dir / "test-results"
        videos = list(video_dir.glob("**/*.webm")) if video_dir.exists() else []

        if videos:
            console.print(f"[green]✓[/green] Video recorded ({len(videos)} videos)")
            checks_passed += 1
        else:
            console.print(f"[yellow]⚠[/yellow] No videos found")

        # Check 6: Report structure is correct
        if "## 🤖 Autonomous QA Report" in report and "### What Was Tested" in report:
            console.print(f"[green]✓[/green] Report has correct structure")
            checks_passed += 1
        else:
            console.print(f"[red]✗[/red] Report structure incorrect")

        # Final result
        console.print(f"\n[bold]Results: {checks_passed}/{total_checks} checks passed[/bold]")

        if checks_passed >= 5:
            console.print("\n[bold green]✅ Autonomous QA Agent Test PASSED![/bold green]")
            console.print("[dim]The agent successfully generates feature-specific tests![/dim]")
            return True
        else:
            console.print("\n[bold red]❌ Autonomous QA Agent Test FAILED[/bold red]")
            console.print("[dim]The agent needs fixes before deployment[/dim]")
            return False

    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed with error:[/bold red]")
        console.print(f"[red]{e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False

    finally:
        # Cleanup
        console.print(f"\n[dim]Cleaning up temporary files...[/dim]")

        # Stop preview server
        try:
            preview_proc.terminate()
            preview_proc.wait(timeout=5)
        except:
            pass

        # Remove temp directory
        try:
            shutil.rmtree(temp_dir)
            console.print(f"[dim]Removed {temp_dir}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not remove {temp_dir}: {e}[/yellow]")


if __name__ == "__main__":
    success = asyncio.run(test_autonomous_qa_agent())
    sys.exit(0 if success else 1)
