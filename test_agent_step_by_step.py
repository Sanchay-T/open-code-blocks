#!/usr/bin/env python3
"""
Step-by-step QA agent with DETAILED LOGGING
Shows exactly what happens at each step
"""
import asyncio
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ob1.github_api import GitHubAPI, RepoRef, parse_github_repo

console = Console()

async def step_by_step_qa():
    """Run QA agent step by step with detailed logging"""

    # Configuration
    PR_NUMBER = 28
    REPO_URL = "https://github.com/Sanchay-T/ob1-sandbox.git"
    WORKTREE = Path("/var/folders/dj/d4sqyptn3t78mw30z8vv9w0w0000gn/T/qa-test-urvqj8x7/sandbox")

    github_token = os.getenv("GITHUB_TOKEN")
    claude_api_key = os.getenv("CLAUDE_API_KEY")

    if not github_token or not claude_api_key:
        console.print("[red]Set GITHUB_TOKEN and CLAUDE_API_KEY[/red]")
        return

    console.print(Panel.fit(
        f"[bold cyan]Step-by-Step QA Agent for PR #{PR_NUMBER}[/bold cyan]\n"
        f"Repository: {REPO_URL}",
        border_style="cyan"
    ))

    # ========================================
    # STEP 1: Fetch PR metadata
    # ========================================
    console.print("\n[bold]📥 STEP 1: Fetch PR Metadata[/bold]")

    owner, repo_name = parse_github_repo(REPO_URL)
    repo_ref = RepoRef(owner=owner, name=repo_name, origin_url=REPO_URL)

    async with GitHubAPI(github_token) as gh:
        pr_data = await gh.get_pull_request(repo_ref, PR_NUMBER)
        files = await gh.list_pull_files(repo_ref, PR_NUMBER)

    console.print(f"[green]✓[/green] PR Title: {pr_data['title']}")
    console.print(f"[green]✓[/green] Author: {pr_data['user']['login']}")
    console.print(f"[green]✓[/green] Changed files: {len(files)}")

    console.print("\n[dim]Changed files:[/dim]")
    for f in files[:10]:
        console.print(f"  [dim]• {f['filename']} (+{f['additions']}/-{f['deletions']})[/dim]")

    # ========================================
    # STEP 2: Identify what was added
    # ========================================
    console.print("\n[bold]🔍 STEP 2: Identify Added Components[/bold]")

    added_components = []
    for f in files:
        filename = f['filename']
        if filename.endswith(('.jsx', '.tsx')) and f['additions'] > f['deletions']:
            component = filename.split('/')[-1].replace('.jsx', '').replace('.tsx', '')
            added_components.append(component)
            console.print(f"[green]✓[/green] Found new component: {component}")

    console.print(f"\n[cyan]Added components: {', '.join(added_components)}[/cyan]")

    # ========================================
    # STEP 3: Read App.jsx to see what's rendered
    # ========================================
    console.print("\n[bold]📖 STEP 3: Read App Entry Point[/bold]")

    app_jsx = WORKTREE / "frontend" / "src" / "App.jsx"
    if app_jsx.exists():
        app_content = app_jsx.read_text()
        console.print(f"[green]✓[/green] Read App.jsx ({len(app_content)} chars)")

        # Show what's in the JSX return statement
        console.print("\n[dim]App.jsx return statement:[/dim]")
        syntax = Syntax(app_content[:500], "jsx", theme="monokai", line_numbers=False)
        console.print(syntax)

        # Detect what's rendered
        has_login = "login" in app_content.lower()
        has_dashboard = "dashboard" in app_content.lower() or "Dashboard" in app_content

        console.print(f"\n[cyan]Analysis:[/cyan]")
        console.print(f"  • Contains login form: {has_login}")
        console.print(f"  • Contains dashboard: {has_dashboard}")

        if has_login and not has_dashboard:
            console.print(f"\n[yellow]⚠ App renders LOGIN FORM only[/yellow]")
            console.print(f"[yellow]⚠ New components ({', '.join(added_components)}) are NOT integrated![/yellow]")
    else:
        console.print("[red]✗ App.jsx not found[/red]")

    # ========================================
    # STEP 4: Determine what to test
    # ========================================
    console.print("\n[bold]🎯 STEP 4: Determine What To Test[/bold]")

    console.print("[cyan]Strategy:[/cyan]")
    console.print("  1. App.jsx only renders login form")
    console.print("  2. Dashboard components exist but aren't wired up")
    console.print("  3. Test what's ACTUALLY accessible: the login form at /")
    console.print("  4. Report that new components aren't integrated")

    test_target = "/"
    test_description = "Login form (actual rendered page)"

    console.print(f"\n[green]✓[/green] Test target: {test_target}")
    console.print(f"[green]✓[/green] Test: {test_description}")

    # ========================================
    # STEP 5: Generate test
    # ========================================
    console.print("\n[bold]🧪 STEP 5: Generate Playwright Test[/bold]")

    test_code = f'''import {{ test, expect }} from '@playwright/test';

test.describe('Login Form', () => {{
  test('login form displays correctly', async ({{ page }}) => {{
    // Navigate to the app
    await page.goto('/');

    // Verify it's the login page
    await expect(page.locator('h1')).toContainText('Sign in');

    // Test login form elements exist
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Fill the form
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');

    // Take screenshot
    await page.screenshot({{ path: 'login-form.png' }});
  }});
}});
'''

    console.print("[green]✓[/green] Generated test code")
    console.print("\n[dim]Test preview:[/dim]")
    syntax = Syntax(test_code[:400], "typescript", theme="monokai", line_numbers=True)
    console.print(syntax)

    # Write test
    test_dir = WORKTREE / "frontend" / "tests" / "qa"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / f"pr-{PR_NUMBER}-login.spec.ts"
    test_file.write_text(test_code)

    console.print(f"\n[green]✓[/green] Test written to: {test_file.name}")

    # ========================================
    # STEP 6: Run test
    # ========================================
    console.print("\n[bold]▶️  STEP 6: Run Playwright Test[/bold]")

    import subprocess

    console.print("[cyan]Running: npx playwright test[/cyan]")
    result = subprocess.run(
        ["npx", "playwright", "test", str(test_file.relative_to(WORKTREE / "frontend"))],
        cwd=str(WORKTREE / "frontend"),
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        console.print("[green]✓ Tests PASSED[/green]")
    else:
        console.print("[yellow]⚠ Tests FAILED[/yellow]")

    console.print(f"\n[dim]Output:[/dim]")
    console.print(result.stdout[:500])

    # ========================================
    # STEP 7: Find videos
    # ========================================
    console.print("\n[bold]📹 STEP 7: Find Recorded Videos[/bold]")

    video_dir = WORKTREE / "frontend" / "test-results"
    videos = list(video_dir.glob("**/*.webm")) if video_dir.exists() else []

    if videos:
        console.print(f"[green]✓[/green] Found {len(videos)} video(s)")
        for v in videos:
            size_kb = v.stat().st_size / 1024
            console.print(f"  [dim]• {v.name} ({size_kb:.1f} KB)[/dim]")

            # Copy to current dir
            import shutil
            dest = Path.cwd() / f"step-by-step-{v.name}"
            shutil.copy2(v, dest)
            console.print(f"  [green]→ Copied to {dest}[/green]")
    else:
        console.print("[red]✗ No videos found[/red]")

    # ========================================
    # STEP 8: Generate report
    # ========================================
    console.print("\n[bold]📝 STEP 8: Generate QA Report[/bold]")

    report = f"""## QA Report for PR #{PR_NUMBER}

### What Was Changed
- Added {len(added_components)} new components: {', '.join(added_components)}

### What Was Tested
- **Target**: Login form at `/`
- **Why**: App.jsx only renders login form - new components not integrated

### Test Results
- **Status**: {"PASSED" if result.returncode == 0 else "FAILED"}
- **Videos**: {len(videos)} recorded

### Findings
⚠️ **New components added but NOT integrated into app**
- Components exist: {', '.join(added_components)}
- App.jsx still only renders login form
- Dashboard components are not accessible

### Recommendation
Wire up the new Dashboard components in App.jsx to make them accessible.
"""

    console.print(Panel(report, border_style="green", title="QA Report"))

    console.print("\n[bold green]✅ Step-by-Step QA Complete![/bold green]")

if __name__ == "__main__":
    asyncio.run(step_by_step_qa())
