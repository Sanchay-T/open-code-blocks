#!/usr/bin/env python3
"""
Efficient Autonomous QA Agent - Minimal context, focused actions

Key principles:
1. Use Haiku for tool execution (cheap, fast)
2. Only Sonnet for final test generation
3. Truncate tool results
4. Clear old context between phases
5. No massive extended thinking budgets
"""
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Optional
from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel

from ob1.github_api import GitHubAPI, RepoRef, parse_github_repo


class EfficientQAAgent:
    """Efficient QA agent with minimal context usage"""

    def __init__(
        self,
        pr_number: int,
        repo_url: str,
        worktree_path: Path,
        github_token: str,
        claude_api_key: str,
        console: Optional[Console] = None
    ):
        self.pr_number = pr_number
        self.repo_url = repo_url
        self.worktree_path = Path(worktree_path)
        self.github_token = github_token
        self.client = Anthropic(api_key=claude_api_key)
        self.console = console or Console()

        owner, repo_name = parse_github_repo(repo_url)
        self.repo_ref = RepoRef(owner=owner, name=repo_name, origin_url=repo_url)

    def get_tools(self) -> list[dict]:
        """Tools with truncation hints"""
        return [
            {
                "name": "get_pr_summary",
                "description": "Get a SUMMARY of PR changes (not full diffs). Returns: title, description, list of changed files with status (added/modified/deleted).",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "read_file",
                "description": "Read a specific file. Returns the file content (use sparingly - only read files you need to test).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to worktree"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "check_routing",
                "description": "Check if a route exists in App.jsx/main routing file. Use this BEFORE writing tests to verify routes are configured. Returns: routing info, whether route exists.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "route": {"type": "string", "description": "Route to check (e.g., '/dashboard')"}
                    },
                    "required": ["route"]
                }
            },
            {
                "name": "run_command",
                "description": "Run a shell command in the worktree. Use for diagnostics like checking dev server status, running builds, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to run"},
                        "cwd": {"type": "string", "description": "Working directory (optional)"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "write_test",
                "description": "Write a Playwright test file. Provide the full test code.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "test_name": {"type": "string", "description": "Test filename (e.g., 'dashboard.spec.ts')"},
                        "test_code": {"type": "string", "description": "Complete Playwright test code"}
                    },
                    "required": ["test_name", "test_code"]
                }
            },
            {
                "name": "run_tests",
                "description": "Run Playwright tests with video recording. Returns: test results, video paths, FULL output for debugging.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "test_file": {"type": "string", "description": "Test file to run (optional - runs all if not specified)"}
                    },
                    "required": []
                }
            },
            {
                "name": "finish",
                "description": "Complete the QA process and return final report.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Summary of QA results"},
                        "test_status": {"type": "string", "description": "PASSED or FAILED"},
                        "recommendations": {"type": "string", "description": "Any recommendations"}
                    },
                    "required": ["summary", "test_status"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute tool with truncated results"""
        self.console.print(f"[cyan]🔧 {tool_name}[/cyan]")

        try:
            if tool_name == "get_pr_summary":
                return await self._get_pr_summary()
            elif tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "check_routing":
                return self._check_routing(tool_input["route"])
            elif tool_name == "run_command":
                return self._run_command(tool_input["command"], tool_input.get("cwd"))
            elif tool_name == "write_test":
                return self._write_test(tool_input["test_name"], tool_input["test_code"])
            elif tool_name == "run_tests":
                return await self._run_tests(tool_input.get("test_file"))
            elif tool_name == "finish":
                return {"finished": True, **tool_input}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    async def _get_pr_summary(self) -> dict[str, Any]:
        """Get PR summary WITHOUT full diffs"""
        async with GitHubAPI(self.github_token) as gh:
            pr_data = await gh.get_pull_request(self.repo_ref, self.pr_number)
            files = await gh.list_pull_files(self.repo_ref, self.pr_number)

        # TRUNCATED - just file list, no diffs
        file_list = []
        for f in files:
            file_list.append({
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"]
            })

        self.console.print(f"[green]   ✓ PR has {len(files)} changed files[/green]")

        return {
            "title": pr_data["title"],
            "description": pr_data.get("body", "")[:500],  # Truncate description
            "files": file_list
        }

    def _read_file(self, path: str) -> dict[str, Any]:
        """Read file with reasonable size limit"""
        file_path = self.worktree_path / path
        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        try:
            content = file_path.read_text()

            # Truncate if too large
            max_size = 3000
            if len(content) > max_size:
                content = content[:max_size] + f"\n... [truncated, total {len(content)} chars]"

            self.console.print(f"[green]   ✓ Read {path}[/green]")
            return {"path": path, "content": content}
        except Exception as e:
            return {"error": str(e)}

    def _check_routing(self, route: str) -> dict[str, Any]:
        """Check if a route exists in App.jsx"""
        app_jsx_path = self.worktree_path / "frontend" / "src" / "App.jsx"

        if not app_jsx_path.exists():
            return {"error": "App.jsx not found"}

        try:
            content = app_jsx_path.read_text()

            # Check if route is mentioned
            route_exists = route in content

            # Look for Route components
            has_router = "BrowserRouter" in content or "Router" in content or "Routes" in content

            # Count routes
            route_count = content.count("<Route")

            self.console.print(f"[green]   ✓ Checked routing for {route}[/green]")
            self.console.print(f"[dim]      Route exists: {route_exists}, Has router: {has_router}, Total routes: {route_count}[/dim]")

            return {
                "route": route,
                "exists": route_exists,
                "has_router": has_router,
                "route_count": route_count,
                "app_jsx_snippet": content[:500]  # First 500 chars
            }
        except Exception as e:
            return {"error": str(e)}

    def _run_command(self, command: str, cwd: Optional[str] = None) -> dict[str, Any]:
        """Run shell command"""
        work_dir = self.worktree_path / cwd if cwd else self.worktree_path

        self.console.print(f"[cyan]   ▶ Running: {command}[/cyan]")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=30
            )

            self.console.print(f"[{'green' if result.returncode == 0 else 'yellow'}]   Exit: {result.returncode}[/{'green' if result.returncode == 0 else 'yellow'}]")

            return {
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:500],
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {"error": str(e)}

    def _write_test(self, test_name: str, test_code: str) -> dict[str, Any]:
        """Write test file"""
        test_dir = self.worktree_path / "frontend" / "tests" / "qa"
        test_dir.mkdir(parents=True, exist_ok=True)

        test_file = test_dir / test_name
        test_file.write_text(test_code)

        self.console.print(f"[green]   ✓ Wrote test: {test_name}[/green]")
        return {"success": True, "path": str(test_file)}

    async def _run_tests(self, test_file: Optional[str]) -> dict[str, Any]:
        """Run Playwright tests with detailed logging"""
        cmd = "npx playwright test"
        if test_file:
            cmd += f" tests/qa/{test_file}"

        self.console.print(f"[cyan]   ▶ {cmd}[/cyan]")

        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(self.worktree_path / "frontend"),
            capture_output=True,
            text=True,
            timeout=120
        )

        # Find videos
        video_dir = self.worktree_path / "frontend" / "test-results"
        videos = list(video_dir.glob("**/*.webm")) if video_dir.exists() else []

        status = "PASSED" if result.returncode == 0 else "FAILED"
        self.console.print(f"[{'green' if result.returncode == 0 else 'yellow'}]   {status}[/{'green' if result.returncode == 0 else 'yellow'}]")

        # Log full output for debugging
        self.console.print(f"[dim]   Full test output (first 2000 chars):[/dim]")
        self.console.print(f"[dim]{result.stdout[:2000]}[/dim]")
        if result.stderr:
            self.console.print(f"[dim]   Stderr: {result.stderr[:1000]}[/dim]")

        return {
            "status": status,
            "exit_code": result.returncode,
            "output": result.stdout[:2000],  # More output for debugging
            "stderr": result.stderr[:1000] if result.stderr else "",
            "videos": [str(v.name) for v in videos],
            "video_count": len(videos)
        }

    async def run(self) -> str:
        """Run efficient QA agent"""
        self.console.print(Panel.fit(
            f"[bold cyan]⚡ Efficient QA Agent[/bold cyan]\nPR #{self.pr_number}",
            border_style="cyan"
        ))

        # Phase 1: Understand PR (use cheap Haiku)
        self.console.print("\n[bold]Phase 1: Analyze PR[/bold]")

        messages = [{
            "role": "user",
            "content": f"""You are a QA agent testing PR #{self.pr_number}.

CRITICAL WORKFLOW (follow exactly):
1. get_pr_summary - see what was changed
2. Read ONLY 1-2 key files to understand features
3. **check_routing** - BEFORE writing tests, check if routes exist in App.jsx
   - If testing /dashboard, use: check_routing with route="/dashboard"
   - This tells you if the route exists or if it will fallback to /
4. Based on routing:
   - If route EXISTS: write test for that route
   - If route DOESN'T exist: test at "/" OR create routing first
5. write_test - create Playwright test
6. run_tests - execute with FULL logging
7. Check test output carefully - did it navigate to the right page?
8. finish - report results

TOOLS:
- get_pr_summary, read_file, check_routing, run_command, write_test, run_tests, finish

CRITICAL: Videos must show NEW features, not login screen!
- Use check_routing to avoid testing non-existent routes
- Log everything for debugging

Start: get_pr_summary"""
        }]

        for iteration in range(10):
            self.console.print(f"\n[dim]Iteration {iteration + 1}/10[/dim]")

            # Use HAIKU for tool execution (cheap)
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4000,
                tools=self.get_tools(),
                messages=messages
            )

            # Check if done
            if response.stop_reason == "end_turn":
                # Extract final text
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                return final_text

            # Handle tool use
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                finished = False

                for block in response.content:
                    if block.type == "tool_use":
                        result = await self.execute_tool(block.name, block.input)

                        # Check if finished
                        if block.name == "finish":
                            finished = True
                            return self._format_report(result)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })

                if finished:
                    break

                messages.append({"role": "user", "content": tool_results})

        return "[yellow]Agent did not complete in 10 iterations[/yellow]"

    def _format_report(self, finish_data: dict) -> str:
        """Format final report"""
        return f"""## QA Report for PR #{self.pr_number}

**Status:** {finish_data.get('test_status', 'UNKNOWN')}

**Summary:**
{finish_data.get('summary', 'No summary provided')}

**Recommendations:**
{finish_data.get('recommendations', 'None')}

---
*Generated by Efficient Autonomous QA Agent*
"""


async def run_efficient_qa(
    pr_number: int,
    repo_url: str,
    worktree_path: Path,
    github_token: str,
    claude_api_key: str,
    console: Optional[Console] = None
) -> str:
    """Entry point"""
    agent = EfficientQAAgent(
        pr_number=pr_number,
        repo_url=repo_url,
        worktree_path=worktree_path,
        github_token=github_token,
        claude_api_key=claude_api_key,
        console=console
    )
    return await agent.run()
