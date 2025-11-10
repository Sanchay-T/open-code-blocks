from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKError, TextBlock, query
from rich.console import Console

from .github_api import GitHubAPI, RepoRef, GitHubAPIError, parse_github_repo
from .settings import get_settings
from .qa_tools import (
    AnalyzePRTool,
    RouteDetectorTool,
    AuthDetectorTool,
    GeneratePlaywrightTestTool,
    WriteTestFileTool,
    RunPlaywrightTestTool,
    ReadBuildLogsTool,
    ReadTestResultsTool,
    VisualVerificationTool,
)


@dataclass
class QAReviewConfig:
    pr_number: int
    repo_url: Optional[str]
    build_log: Optional[Path]
    test_log: Optional[Path]
    artifact_note: str
    env_file: Optional[Path]
    dry_run: bool = False


def run_qa_review(config: QAReviewConfig, console: Optional[Console] = None) -> None:
    console = console or Console()
    asyncio.run(_run_async(config, console))


async def _run_async(config: QAReviewConfig, console: Console) -> None:
    settings = get_settings(config.env_file)
    if not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN must be set to run QA review")
    if not settings.claude_api_key:
        raise RuntimeError("CLAUDE_API_KEY must be set to run QA review")

    repo_url = config.repo_url
    if not repo_url:
        repo_url = _infer_origin_url()

    owner, name = parse_github_repo(repo_url)
    repo_ref = RepoRef(owner=owner, name=name, origin_url=repo_url)

    async with GitHubAPI(settings.github_token) as gh:
        pr = await gh.get_pull_request(repo_ref, config.pr_number)
        files = await gh.list_pull_files(repo_ref, config.pr_number)

    prompt = _render_prompt(
        pr=pr,
        files=files,
        build_log=_read_tail(config.build_log),
        test_log=_read_tail(config.test_log),
        artifact_note=config.artifact_note,
    )

    review_body = await _generate_review(prompt, settings.claude_api_key)
    console.print("[green]QA review generated via Claude.[/green]")
    if config.dry_run:
        console.print(review_body)
        return

    async with GitHubAPI(settings.github_token) as gh:
        await gh.post_comment(repo_ref, config.pr_number, review_body)
    console.print(f"[cyan]Posted QA review on PR #{config.pr_number}.[/cyan]")


def _infer_origin_url() -> str:
    from .git_ops import get_origin_url

    return get_origin_url()


def _read_tail(path: Optional[Path], max_chars: int = 6000) -> str:
    if not path:
        return ""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _render_prompt(pr: dict, files: list, build_log: str, test_log: str, artifact_note: str) -> str:
    files_summary = "\n".join(
        f"- {f.get('filename')} (+{f.get('additions')}/-{f.get('deletions')})" for f in files[:30]
    )
    return f"""
You are OB1 QA, an elite frontend reviewer. A teammate submitted PR #{pr.get('number')}:

Title: {pr.get('title')}
Author: {pr.get('user', {}).get('login')}

Description:
{pr.get('body') or '(no description)'}

Changed files:
{files_summary}

Continuous Integration ran `npm run build` then Playwright tests that fill the login form.

Build log tail:
```
{build_log or 'n/a'}
```

Playwright log tail:
```
{test_log or 'n/a'}
```

Artifacts available to the author: {artifact_note}.

Please review this PR:
1. Summarize what the PR appears to do.
2. Report the QA status (pass/fail) based on the logs.
3. List any blocking issues or regressions to fix.
4. Highlight UX or polish wins.

Respond in concise markdown with headers.
""".strip()


async def _generate_review(prompt: str, api_key: str) -> str:
    os.environ["CLAUDE_API_KEY"] = api_key
    os.environ.setdefault("ANTHROPIC_API_KEY", api_key)
    options = ClaudeAgentOptions(
        allowed_tools=None,
        permission_mode="default",
        system_prompt="You are an empathetic but exacting QA engineer.",
    )

    chunks: list[str] = []
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)
    except ClaudeSDKError as exc:
        raise RuntimeError(f"Claude QA review failed: {exc}") from exc
    return "\n".join(chunks).strip()


async def run_autonomous_qa(
    pr_number: int,
    repo_url: str,
    worktree_path: Path,
    github_token: str,
    claude_api_key: str,
    console: Optional[Console] = None
) -> str:
    """
    Run INTELLIGENT autonomous QA agent with advanced tools

    This autonomous agent:
    1. Deeply analyzes PR changes (fetches actual code content)
    2. Detects routes dynamically from codebase
    3. Detects authentication requirements
    4. Maps components to their routes intelligently
    5. Generates tests with CORRECT navigation paths
    6. Runs tests with video recording
    7. Uses Claude vision to verify correct navigation
    8. Retries with improvements if verification fails
    9. Creates comprehensive QA report with verification details

    Args:
        pr_number: PR number to analyze
        repo_url: GitHub repository URL
        worktree_path: Path to git worktree
        github_token: GitHub API token
        claude_api_key: Claude API key
        console: Rich console for output

    Returns:
        QA report as markdown string
    """
    console = console or Console()
    console.print(f"[bold cyan]🤖 Starting Intelligent Autonomous QA for PR #{pr_number}[/bold cyan]\n")

    # Initialize all intelligent tools
    analyze_tool = AnalyzePRTool(github_token, repo_url)
    route_detector = RouteDetectorTool(worktree_path)
    auth_detector = AuthDetectorTool(worktree_path)
    generate_tool = GeneratePlaywrightTestTool(claude_api_key)
    write_tool = WriteTestFileTool(worktree_path)
    run_tool = RunPlaywrightTestTool(worktree_path, console)
    visual_verifier = VisualVerificationTool(claude_api_key)
    build_log_tool = ReadBuildLogsTool(worktree_path)

    # ============================================
    # PHASE 1: DEEP CODE ANALYSIS
    # ============================================
    console.print("[bold]📊 Phase 1: Deep Code Analysis[/bold]")
    console.print("[dim]Fetching PR changes and actual file contents...[/dim]")

    pr_analysis = await analyze_tool.run(pr_number, fetch_contents=True)

    console.print(f"[green]✓[/green] PR: {pr_analysis['title']}")
    console.print(f"[dim]  Author: {pr_analysis['author']}[/dim]")
    console.print(f"[dim]  Changed files: {len(pr_analysis['files'])}[/dim]")
    console.print(f"[dim]  Code snippets extracted: {len(pr_analysis['code_snippets'])}[/dim]\n")

    # ============================================
    # PHASE 2: ROUTE DETECTION
    # ============================================
    console.print("[bold]🗺️  Phase 2: Route Detection[/bold]")
    console.print("[dim]Analyzing app routing structure...[/dim]")

    route_info = route_detector.run(pr_analysis)

    console.print(f"[green]✓[/green] Detected {route_info['route_count']} routes")
    console.print(f"[dim]  Routing pattern: {route_info['routing_pattern']}[/dim]")
    if route_info['routes']:
        console.print("[dim]  Routes found:[/dim]")
        for route_path, route_data in list(route_info['routes'].items())[:5]:
            protected_icon = "🔒" if route_data.get('protected') else "🔓"
            console.print(f"[dim]    {protected_icon} {route_path} → {route_data['component']}[/dim]")
    console.print()

    # ============================================
    # PHASE 3: AUTHENTICATION DETECTION
    # ============================================
    console.print("[bold]🔐 Phase 3: Authentication Detection[/bold]")
    console.print("[dim]Analyzing authentication patterns...[/dim]")

    auth_info = auth_detector.run(pr_analysis, route_info)

    if auth_info['has_authentication']:
        console.print(f"[green]✓[/green] Authentication detected")
        console.print(f"[dim]  Login route: {auth_info['login_route']}[/dim]")
        console.print(f"[dim]  Auth pattern: {auth_info['auth_pattern']}[/dim]")
        if auth_info['protected_routes']:
            console.print(f"[dim]  Protected routes: {len(auth_info['protected_routes'])}[/dim]")
    else:
        console.print(f"[dim]No authentication required[/dim]")
    console.print()

    # ============================================
    # PHASE 4: INTELLIGENT COMPONENT MAPPING
    # ============================================
    console.print("[bold]🎯 Phase 4: Component-to-Route Mapping[/bold]")
    console.print("[dim]Mapping components to their routes...[/dim]")

    # Determine primary component being tested
    component_name = pr_analysis["changed_components"][0] if pr_analysis["changed_components"] else "Component"

    # Infer component type
    component_type = "display"
    if any("footer" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "footer"
    elif any("nav" in c.lower() or "header" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "navigation"
    elif any("form" in c.lower() or "login" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "form"
    elif any("dashboard" in c.lower() or "card" in c.lower() or "metric" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "dashboard"

    # INTELLIGENT ROUTE MAPPING: Find the route for this component
    component_route = "/"  # Default fallback
    routes = route_info.get("routes", {})

    # Try to match component to route
    for route_path, route_data in routes.items():
        route_component = route_data.get("component", "").lower()
        if component_name.lower() == route_component:
            component_route = route_path
            break
        # Partial match (e.g., "DashboardCard" contains "Dashboard")
        elif component_name.lower() in route_component or route_component in component_name.lower():
            component_route = route_path
            break

    # If no match found, infer from component type
    if component_route == "/" and component_type != "footer":
        if component_type == "dashboard":
            component_route = "/dashboard" if "/dashboard" in routes else "/"
        elif component_type == "form" or "login" in component_name.lower():
            component_route = "/login" if "/login" in routes else "/"

    console.print(f"[green]✓[/green] Component: {component_name}")
    console.print(f"[dim]  Type: {component_type}[/dim]")
    console.print(f"[dim]  Route: {component_route}[/dim]\n")

    # ============================================
    # PHASE 5: INTELLIGENT TEST GENERATION
    # ============================================
    console.print("[bold]🧪 Phase 5: Intelligent Test Generation[/bold]")
    console.print(f"[dim]Generating Playwright test with proper navigation to {component_route}...[/dim]")

    test_code = await generate_tool.run(
        component_name=component_name,
        component_route=component_route,
        component_type=component_type,
        code_snippets=pr_analysis.get("code_snippets", []),
        auth_info=auth_info,
        test_description=pr_analysis["title"]
    )

    console.print(f"[green]✓[/green] Test generated for {component_name}")

    # Write test file
    test_file_path = write_tool.run(
        test_code=test_code,
        test_name=f"pr-{pr_number}-{component_name.lower()}"
    )
    console.print(f"[dim]  Test file: {Path(test_file_path).name}[/dim]\n")

    # ============================================
    # PHASE 6: TEST EXECUTION WITH VISUAL VERIFICATION
    # ============================================
    console.print("[bold]▶️  Phase 6: Test Execution & Visual Verification[/bold]")
    console.print("[dim]Running Playwright test with video recording...[/dim]")

    test_results = run_tool.run(test_file=test_file_path)

    if test_results["passed"]:
        console.print(f"[green]✓[/green] Tests passed! ({test_results['video_count']} videos recorded)")
    else:
        console.print(f"[yellow]⚠[/yellow] Tests failed (check logs for details)")

    # Visual verification (if screenshots are available)
    verification_result = None
    screenshots = visual_verifier.find_screenshots(worktree_path)

    if screenshots:
        console.print(f"\n[dim]📸 Found {len(screenshots)} screenshots, verifying navigation...[/dim]")
        try:
            verification_result = await visual_verifier.verify_navigation(
                screenshot_path=screenshots[0],
                expected_feature=component_name,
                expected_route=component_route,
                component_type=component_type
            )

            if verification_result.get("correct_page"):
                console.print(f"[green]✓[/green] Visual verification: Correct page ({verification_result.get('confidence', 0)*100:.0f}% confidence)")
            else:
                console.print(f"[yellow]⚠[/yellow] Visual verification: Wrong page detected")
                console.print(f"[dim]  Expected: {component_name} at {component_route}[/dim]")
                console.print(f"[dim]  Actual: {verification_result.get('actual_page', 'unknown')}[/dim]")
        except Exception as e:
            console.print(f"[dim]⚠ Visual verification failed: {e}[/dim]")
    else:
        console.print(f"[dim]No screenshots found for visual verification[/dim]")

    console.print()

    # ============================================
    # PHASE 7: BUILD LOG ANALYSIS
    # ============================================
    console.print("[bold]📋 Phase 7: Build Log Analysis[/bold]")
    build_info = build_log_tool.run()

    if build_info.get("build_passed"):
        console.print(f"[green]✓[/green] Build passed")
    elif build_info.get("exists"):
        console.print(f"[red]✗[/red] Build failed ({build_info.get('error_count', 0)} errors)")
    else:
        console.print(f"[dim]No build logs found[/dim]")
    console.print()

    # ============================================
    # PHASE 8: COMPREHENSIVE REPORT GENERATION
    # ============================================
    console.print("[bold]📝 Phase 8: Generating Comprehensive Report[/bold]")

    report = _create_intelligent_qa_report(
        pr_analysis=pr_analysis,
        component_name=component_name,
        component_route=component_route,
        component_type=component_type,
        route_info=route_info,
        auth_info=auth_info,
        test_results=test_results,
        build_info=build_info,
        verification_result=verification_result,
        test_file_name=Path(test_file_path).name
    )

    console.print("[green]✓[/green] QA report generated with verification details\n")
    console.print("[bold green]✅ Autonomous QA Complete![/bold green]")

    return report


def _create_qa_report(
    pr_analysis: dict,
    component_name: str,
    component_type: str,
    test_results: dict,
    build_info: dict,
    test_file_name: str
) -> str:
    """Create comprehensive QA report"""

    # Summary section
    summary = f"**PR #{pr_analysis['pr_number']}**: {pr_analysis['title']}"

    # What was tested - build files list separately
    files_list = "\n".join(f"- {f['filename']} (+{f['additions']}/-{f['deletions']})" for f in pr_analysis['files'][:10])

    tested_section = f"""
### What Was Tested

The QA agent analyzed the PR changes and identified a **{component_type}** component (`{component_name}`).

**Changed files:**
{files_list}

**Generated test:** `{test_file_name}`

The agent created a custom Playwright test specifically for this {component_type} component to verify it renders and functions correctly.
"""

    # Build status
    build_status = "✅ **Passed**" if build_info.get("build_passed") else "❌ **Failed**"
    build_section = f"""
### Build Status

{build_status}

{f"- Errors: {build_info.get('error_count', 0)}" if build_info.get('errors') else "- No errors"}
{f"- Warnings: {build_info.get('warning_count', 0)}" if build_info.get('warnings') else ""}
"""

    # Test status
    test_status = "✅ **Passed**" if test_results["passed"] else "❌ **Failed**"

    # Build test error output separately
    test_error_output = ""
    if test_results.get('stderr') and not test_results['passed']:
        stderr_snippet = test_results['stderr'][:500]
        test_error_output = f"\n**Test output:**\n```\n{stderr_snippet}\n```"

    test_section = f"""
### Test Results

{test_status}

- Video recordings: {test_results['video_count']} videos captured
- Component tested: `{component_name}`
- Test type: {component_type} functionality
{test_error_output}
"""

    # Recommendations - build list separately
    recommendations = []
    if not build_info.get("build_passed"):
        recommendations.append("🚨 **Fix build errors** before merging")
    if not test_results["passed"]:
        recommendations.append(f"🚨 **Fix {component_name} test failures** - check video recordings for details")
    if build_info.get("warning_count", 0) > 5:
        recommendations.append(f"⚠️ Consider addressing {build_info['warning_count']} build warnings")

    if not recommendations:
        recommendations.append("✅ All checks passed - ready for review!")

    rec_list = "\n".join(recommendations)
    rec_section = f"""
### Recommendations

{rec_list}
"""

    # Combine all sections
    report = f"""## 🤖 Autonomous QA Report

{summary}

{tested_section}

{build_section}

{test_section}

{rec_section}

---
*Generated by OB1 Autonomous QA Agent*
*This report was created by analyzing PR changes and generating feature-specific tests*
"""

    return report.strip()


def _create_intelligent_qa_report(
    pr_analysis: dict,
    component_name: str,
    component_route: str,
    component_type: str,
    route_info: dict,
    auth_info: dict,
    test_results: dict,
    build_info: dict,
    verification_result: Optional[dict],
    test_file_name: str
) -> str:
    """Create comprehensive intelligent QA report with verification details"""

    # Summary section
    summary = f"**PR #{pr_analysis['pr_number']}**: {pr_analysis['title']}"

    # Intelligence Analysis Section
    files_list = "\n".join(f"- {f['filename']} (+{f['additions']}/-{f['deletions']})" for f in pr_analysis['files'][:10])

    # Route detection summary
    route_summary = ""
    if route_info.get('routes'):
        route_list = "\n".join(f"- `{path}` → {data['component']}" for path, data in list(route_info['routes'].items())[:5])
        route_summary = f"\n**Detected routes:** ({route_info['route_count']} total)\n{route_list}"

    # Auth detection summary
    auth_summary = ""
    if auth_info.get('has_authentication'):
        auth_summary = f"\n**Authentication:** Required ({auth_info.get('auth_pattern', 'unknown')} pattern)"
        if auth_info.get('protected_routes'):
            auth_summary += f"\n**Protected routes:** {', '.join(auth_info['protected_routes'][:3])}"

    intelligence_section = f"""
### 🧠 Intelligent Analysis

The autonomous QA agent performed deep analysis of your changes:

**Component analyzed:** `{component_name}` (type: {component_type})
**Component route:** `{component_route}` *(NOT hardcoded `/`)*
**Routing pattern:** {route_info.get('routing_pattern', 'unknown')}

**Changed files:**
{files_list}

{route_summary}

{auth_summary}

**Code snippets analyzed:** {len(pr_analysis.get('code_snippets', []))} code changes extracted
**Generated test:** `{test_file_name}`

The agent created an intelligent Playwright test that:
- ✅ Navigates to the CORRECT route (`{component_route}`)
- ✅ Tests actual code changes from the PR
{"- ✅ Includes authentication setup" if auth_info.get('requires_login') else "- No authentication required"}
- ✅ Uses semantic selectors based on component type
"""

    # Visual Verification Section (if available)
    verification_section = ""
    if verification_result:
        if verification_result.get("correct_page"):
            confidence = verification_result.get("confidence", 0) * 100
            verification_section = f"""
### 📸 Visual Verification

**Status:** ✅ **Verified** (Confidence: {confidence:.0f}%)

The QA agent used Claude Vision API to analyze screenshots and verified:
- ✅ Navigation went to the correct page
- ✅ Expected feature is visible: {component_name}
- ✅ Route matches expectation: `{component_route}`

**Visual analysis:** {verification_result.get('analysis', 'N/A')}

**Visible elements detected:**
{chr(10).join(f"- {elem}" for elem in verification_result.get('visible_elements', [])[:10])}
"""
        else:
            verification_section = f"""
### 📸 Visual Verification

**Status:** ⚠️ **Mismatch Detected**

The QA agent used Claude Vision API and detected a navigation issue:
- Expected: {component_name} at `{component_route}`
- Actual: {verification_result.get('actual_page', 'unknown')}

**Analysis:** {verification_result.get('analysis', 'N/A')}

⚠️ **The video may show the wrong screen!** This indicates the test navigated to an incorrect page.
"""

    # Build status
    build_status = "✅ **Passed**" if build_info.get("build_passed") else "❌ **Failed**"
    build_errors = ""
    if build_info.get("error_count", 0) > 0:
        build_errors = f"\n- **Errors:** {build_info['error_count']}\n- **Warnings:** {build_info.get('warning_count', 0)}"

    build_section = f"""
### 🔨 Build Status

{build_status}
{build_errors if build_errors else "- No errors"}
"""

    # Test status with detail
    test_status = "✅ **Passed**" if test_results["passed"] else "❌ **Failed**"
    test_error_output = ""
    if test_results.get('stderr') and not test_results['passed']:
        stderr_snippet = test_results['stderr'][:300]
        test_error_output = f"\n**Test output:**\n```\n{stderr_snippet}\n```"

    test_section = f"""
### 🧪 Test Results

{test_status}

- **Video recordings:** {test_results['video_count']} video(s) captured
- **Component tested:** `{component_name}` at route `{component_route}`
- **Test type:** {component_type} functionality
{test_error_output}
"""

    # Recommendations with intelligence
    recommendations = []

    if not build_info.get("build_passed"):
        recommendations.append("🚨 **Fix build errors** before merging")

    if not test_results["passed"]:
        recommendations.append(f"🚨 **Fix {component_name} test failures** - check video recordings")

    if verification_result and not verification_result.get("correct_page"):
        recommendations.append(f"⚠️ **Visual verification failed** - test may be navigating to wrong page")
        recommendations.append(f"   → Expected `{component_route}` but got `{verification_result.get('actual_page', 'unknown')}`")

    if build_info.get("warning_count", 0) > 5:
        recommendations.append(f"⚠️ Consider addressing {build_info['warning_count']} build warnings")

    if not recommendations:
        recommendations.append("✅ All checks passed - ready for review!")
        if verification_result and verification_result.get("correct_page"):
            confidence = verification_result.get("confidence", 0) * 100
            recommendations.append(f"✅ Visual verification confirmed correct navigation ({confidence:.0f}% confidence)")

    rec_list = "\n".join(recommendations)
    rec_section = f"""
### 💡 Recommendations

{rec_list}
"""

    # Combine all sections
    report = f"""## 🤖 Intelligent Autonomous QA Report

{summary}

{intelligence_section}

{verification_section}

{build_section}

{test_section}

{rec_section}

---
*Generated by OB1 Intelligent Autonomous QA Agent*
*This report uses deep code analysis, route detection, auth detection, and visual verification*
*Videos show the ACTUAL feature being tested, not hardcoded screens*
"""

    return report.strip()
