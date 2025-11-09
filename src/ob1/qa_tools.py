"""
QA Agent Tools - Provides autonomous QA agent with tools to analyze PRs and generate tests
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import AssistantMessage, TextBlock, query as claude_query
from rich.console import Console

from .github_api import GitHubAPI, RepoRef, parse_github_repo


class AnalyzePRTool:
    """Tool to analyze PR changes and understand what feature was added"""

    name = "analyze_pr"
    description = "Analyzes a Pull Request to understand what files changed and what feature was added. Returns PR metadata, changed files, and diff content."

    def __init__(self, github_token: str, repo_url: str):
        self.github_token = github_token
        self.repo_url = repo_url
        self.owner, self.repo_name = parse_github_repo(repo_url)

    async def run(self, pr_number: int) -> dict[str, Any]:
        """
        Fetch PR data from GitHub API

        Args:
            pr_number: Pull request number

        Returns:
            Dict with pr_data, files, and analysis
        """
        repo_ref = RepoRef(owner=self.owner, name=self.repo_name, origin_url=self.repo_url)

        async with GitHubAPI(self.github_token) as gh:
            pr_data = await gh.get_pull_request(repo_ref, pr_number)
            files = await gh.list_pull_files(repo_ref, pr_number)

        # Extract component/feature information from changed files
        changed_components = []
        file_types = {"jsx": 0, "tsx": 0, "css": 0, "js": 0, "ts": 0}

        for file in files:
            filename = file.get("filename", "")
            if "/" in filename:
                component_name = filename.split("/")[-1].replace(".jsx", "").replace(".tsx", "").replace(".css", "")
                changed_components.append(component_name)

            # Track file types
            for ext in file_types:
                if filename.endswith(f".{ext}"):
                    file_types[ext] += 1

        return {
            "pr_number": pr_number,
            "title": pr_data.get("title", ""),
            "description": pr_data.get("body", ""),
            "author": pr_data.get("user", {}).get("login", ""),
            "files": files,
            "changed_components": list(set(changed_components)),
            "file_types": file_types,
            "total_additions": sum(f.get("additions", 0) for f in files),
            "total_deletions": sum(f.get("deletions", 0) for f in files),
        }


class GeneratePlaywrightTestTool:
    """Tool to generate Playwright test code based on component analysis"""

    name = "generate_playwright_test"
    description = "Generates Playwright test code for a specific component or feature. Takes component info and returns valid TypeScript test code."

    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key

    async def run(
        self,
        component_name: str,
        component_type: str,
        changed_files: list[str],
        test_description: Optional[str] = None
    ) -> str:
        """
        Generate Playwright test code using Claude

        Args:
            component_name: Name of the component (e.g., "Footer", "Dashboard")
            component_type: Type of component (e.g., "footer", "navigation", "form", "display")
            changed_files: List of changed file paths
            test_description: Optional description of what to test

        Returns:
            Valid Playwright TypeScript test code
        """
        files_list = "\n".join(f"- {f}" for f in changed_files[:10])

        prompt = f"""Generate a Playwright test for a React component.

Component: {component_name}
Type: {component_type}
Changed files:
{files_list}

{f"Test description: {test_description}" if test_description else ""}

Generate a complete Playwright test that:
1. Navigates to the page
2. Tests that the {component_name} component renders
3. Tests key functionality of the component
4. Uses appropriate selectors (prefer data-testid, or semantic selectors)
5. Includes assertions for visibility and content

Return ONLY the TypeScript test code, no explanation.

Example structure:
```typescript
import {{ test, expect }} from '@playwright/test';

test('{component_name.lower()} displays correctly', async ({{ page }}) => {{
  await page.goto('/');
  // Add your test code here
}});
```

Generate the complete test now:"""

        # Set API key in environment
        os.environ["CLAUDE_API_KEY"] = self.claude_api_key
        os.environ.setdefault("ANTHROPIC_API_KEY", self.claude_api_key)

        # Use claude-agent-sdk query
        chunks = []
        async for message in claude_query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)

        test_code = "\n".join(chunks).strip()

        # Clean up markdown code blocks if present
        if "```typescript" in test_code:
            test_code = test_code.split("```typescript")[1].split("```")[0].strip()
        elif "```ts" in test_code:
            test_code = test_code.split("```ts")[1].split("```")[0].strip()
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0].strip()

        return test_code


class WriteTestFileTool:
    """Tool to write generated test code to a file"""

    name = "write_test_file"
    description = "Writes Playwright test code to a file in the tests/qa directory. Returns the file path."

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path
        self.test_dir = worktree_path / "frontend" / "tests" / "qa"

    def run(self, test_code: str, test_name: str) -> str:
        """
        Write test code to file

        Args:
            test_code: TypeScript test code
            test_name: Name for the test file (without .spec.ts extension)

        Returns:
            Absolute path to created test file
        """
        # Ensure test directory exists
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Create test file
        test_file = self.test_dir / f"{test_name}.spec.ts"
        test_file.write_text(test_code, encoding="utf-8")

        return str(test_file)


class RunPlaywrightTestTool:
    """Tool to execute Playwright tests and capture results"""

    name = "run_playwright_test"
    description = "Runs Playwright tests and returns the results with video paths. Can run specific test file or all tests."

    def __init__(self, worktree_path: Path, console: Optional[Console] = None):
        self.worktree_path = worktree_path
        self.frontend_dir = worktree_path / "frontend"
        self.console = console or Console()

    def run(self, test_file: Optional[str] = None) -> dict[str, Any]:
        """
        Execute Playwright tests

        Args:
            test_file: Optional specific test file to run. If None, runs all tests.

        Returns:
            Dict with test results, exit code, stdout, stderr, and video paths
        """
        # Build command
        cmd = ["npx", "playwright", "test"]
        if test_file:
            # Get relative path from frontend dir
            if test_file.startswith(str(self.frontend_dir)):
                rel_path = Path(test_file).relative_to(self.frontend_dir)
                cmd.append(str(rel_path))
            else:
                cmd.append(test_file)

        self.console.print(f"[dim cyan]Running:[/dim cyan] {' '.join(cmd)}")

        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.frontend_dir),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            # Find video files
            video_dir = self.frontend_dir / "test-results"
            videos = []
            if video_dir.exists():
                videos = [str(p) for p in video_dir.glob("**/*.webm")]

            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "videos": videos,
                "video_count": len(videos)
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "passed": False,
                "stdout": "",
                "stderr": "Test execution timed out after 2 minutes",
                "videos": [],
                "video_count": 0
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "passed": False,
                "stdout": "",
                "stderr": str(e),
                "videos": [],
                "video_count": 0
            }


class ReadBuildLogsTool:
    """Tool to read and parse build logs"""

    name = "read_build_logs"
    description = "Reads build logs and extracts errors, warnings, and build status."

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path

    def run(self, log_file: str = "build.log", max_lines: int = 100) -> dict[str, Any]:
        """
        Read and parse build logs

        Args:
            log_file: Path to build log file (relative to worktree)
            max_lines: Maximum number of lines to read from end

        Returns:
            Dict with build status, errors, warnings, and log tail
        """
        log_path = self.worktree_path / log_file

        if not log_path.exists():
            return {
                "exists": False,
                "build_passed": None,
                "errors": [],
                "warnings": [],
                "log_tail": ""
            }

        # Read log file
        log_content = log_path.read_text(encoding="utf-8", errors="ignore")
        lines = log_content.splitlines()

        # Get tail
        tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        tail = "\n".join(tail_lines)

        # Parse for errors and warnings
        errors = [line for line in lines if "error" in line.lower() and not line.strip().startswith("//")]
        warnings = [line for line in lines if "warning" in line.lower() and not line.strip().startswith("//")]

        # Determine build status
        build_passed = "build complete" in log_content.lower() or "built in" in log_content.lower()
        build_failed = "build failed" in log_content.lower() or len(errors) > 0

        return {
            "exists": True,
            "build_passed": build_passed and not build_failed,
            "errors": errors[:10],  # First 10 errors
            "warnings": warnings[:10],  # First 10 warnings
            "error_count": len(errors),
            "warning_count": len(warnings),
            "log_tail": tail
        }


class ReadTestResultsTool:
    """Tool to read and parse Playwright test results"""

    name = "read_test_results"
    description = "Reads Playwright test results and extracts test status, passed/failed tests, and errors."

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path

    def run(self, log_file: str = "playwright.log", max_lines: int = 100) -> dict[str, Any]:
        """
        Read and parse test results

        Args:
            log_file: Path to test log file (relative to worktree)
            max_lines: Maximum number of lines to read from end

        Returns:
            Dict with test status, passed/failed counts, and log tail
        """
        log_path = self.worktree_path / log_file

        if not log_path.exists():
            return {
                "exists": False,
                "tests_passed": None,
                "passed_count": 0,
                "failed_count": 0,
                "tests": [],
                "log_tail": ""
            }

        # Read log file
        log_content = log_path.read_text(encoding="utf-8", errors="ignore")
        lines = log_content.splitlines()

        # Get tail
        tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        tail = "\n".join(tail_lines)

        # Parse test results
        passed_tests = []
        failed_tests = []

        for line in lines:
            if "✓" in line or "passed" in line.lower():
                passed_tests.append(line.strip())
            elif "✗" in line or "failed" in line.lower():
                failed_tests.append(line.strip())

        # Determine overall status
        all_passed = "passed" in log_content.lower() and failed_tests == []

        return {
            "exists": True,
            "tests_passed": all_passed,
            "passed_count": len(passed_tests),
            "failed_count": len(failed_tests),
            "passed_tests": passed_tests[:5],
            "failed_tests": failed_tests[:5],
            "log_tail": tail
        }
