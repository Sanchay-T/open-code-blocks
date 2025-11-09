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
    GeneratePlaywrightTestTool,
    WriteTestFileTool,
    RunPlaywrightTestTool,
    ReadBuildLogsTool,
    ReadTestResultsTool,
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
    Run autonomous QA agent with tools to analyze PR, generate tests, run them, and report

    This is the new autonomous agent that:
    1. Analyzes PR changes to understand what feature was added
    2. Generates appropriate Playwright tests for the feature
    3. Runs the tests with video recording
    4. Reviews build logs and test results
    5. Creates comprehensive QA report

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
    console.print(f"[cyan]Starting autonomous QA for PR #{pr_number}[/cyan]")

    # Initialize tools
    analyze_tool = AnalyzePRTool(github_token, repo_url)
    generate_tool = GeneratePlaywrightTestTool(claude_api_key)
    write_tool = WriteTestFileTool(worktree_path)
    run_tool = RunPlaywrightTestTool(worktree_path, console)
    build_log_tool = ReadBuildLogsTool(worktree_path)
    test_results_tool = ReadTestResultsTool(worktree_path)

    # Step 1: Analyze PR
    console.print("[dim]📊 Analyzing PR changes...[/dim]")
    pr_analysis = await analyze_tool.run(pr_number)

    console.print(f"[green]✓[/green] PR: {pr_analysis['title']}")
    console.print(f"[dim]  Changed components: {', '.join(pr_analysis['changed_components'][:5])}[/dim]")

    # Step 2: Determine what to test based on PR changes
    components_str = ", ".join(pr_analysis["changed_components"][:3])
    component_name = pr_analysis["changed_components"][0] if pr_analysis["changed_components"] else "Component"

    # Infer component type from file changes
    component_type = "display"
    if any("footer" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "footer"
    elif any("nav" in c.lower() or "header" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "navigation"
    elif any("form" in c.lower() or "login" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "form"
    elif any("dashboard" in c.lower() or "card" in c.lower() for c in pr_analysis["changed_components"]):
        component_type = "dashboard"

    # Step 3: Generate test code
    console.print(f"[dim]🧪 Generating Playwright test for {component_name}...[/dim]")

    changed_files = [f["filename"] for f in pr_analysis["files"][:10]]
    test_code = await generate_tool.run(
        component_name=component_name,
        component_type=component_type,
        changed_files=changed_files,
        test_description=pr_analysis["title"]
    )

    console.print(f"[green]✓[/green] Generated test for {component_name}")

    # Step 4: Write test file
    test_file_path = write_tool.run(
        test_code=test_code,
        test_name=f"pr-{pr_number}-{component_name.lower()}"
    )

    console.print(f"[dim]  Test file: {Path(test_file_path).name}[/dim]")

    # Step 5: Run the test
    console.print(f"[dim]▶️  Running Playwright test...[/dim]")
    test_results = run_tool.run(test_file=test_file_path)

    if test_results["passed"]:
        console.print(f"[green]✓[/green] Tests passed! ({test_results['video_count']} videos recorded)")
    else:
        console.print(f"[yellow]⚠[/yellow] Tests failed")

    # Step 6: Read build logs
    build_info = build_log_tool.run()

    # Step 7: Create comprehensive QA report
    report = _create_qa_report(
        pr_analysis=pr_analysis,
        component_name=component_name,
        component_type=component_type,
        test_results=test_results,
        build_info=build_info,
        test_file_name=Path(test_file_path).name
    )

    console.print("[green]✓[/green] QA report generated")

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
