#!/usr/bin/env python3
"""
Smart QA Agent with Memory, Blocker Detection, and Developer Handoff

Features:
1. Detects blockers (missing routes, broken builds, etc.)
2. Comments on PR with structured issue report
3. Remembers previous issues and checks if fixed
4. Generates developer-friendly fix instructions
5. Resumes testing once blockers are resolved
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Optional, Dict
from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel

from ob1.github_api import GitHubAPI, RepoRef, parse_github_repo


class SmartQAAgent:
    """Smart QA agent with memory and blocker handling"""

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

        # State file for memory
        self.state_file = Path(f".qa_state_pr_{pr_number}.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load previous QA state for this PR"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "pr_number": self.pr_number,
            "attempts": [],
            "known_issues": [],
            "last_status": None
        }

    def _save_state(self):
        """Save QA state"""
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def get_tools(self) -> list[dict]:
        """QA tools with blocker detection"""
        return [
            {
                "name": "get_pr_info",
                "description": "Get PR metadata and previous QA state. Returns: PR changes, previous blockers, what to check.",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "analyze_integration",
                "description": "Check if new code is properly integrated (routes exist, components wired up, etc.). Returns: integration status, blockers found.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of component names to check"
                        }
                    },
                    "required": ["component_names"]
                }
            },
            {
                "name": "report_blocker",
                "description": "Report a blocker that prevents QA testing. This posts a comment on the PR and generates a fix guide for developers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "blocker_type": {
                            "type": "string",
                            "description": "Type of blocker (e.g., 'missing_routing', 'build_error', 'missing_dependencies')"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the blocker"
                        },
                        "fix_instructions": {
                            "type": "string",
                            "description": "Step-by-step instructions for developer to fix"
                        },
                        "files_to_modify": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files that need to be modified"
                        }
                    },
                    "required": ["blocker_type", "description", "fix_instructions"]
                }
            },
            {
                "name": "run_qa_tests",
                "description": "Run QA tests (only use AFTER verifying no blockers exist). Returns test results and videos.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "test_strategy": {
                            "type": "string",
                            "description": "Strategy for testing (e.g., 'test_at_route', 'test_harness', 'component_tests')"
                        }
                    },
                    "required": ["test_strategy"]
                }
            },
            {
                "name": "finish_qa",
                "description": "Complete QA process with final report.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "QA status: 'PASSED', 'FAILED', 'BLOCKED'"
                        },
                        "summary": {"type": "string"},
                        "next_steps": {"type": "string", "description": "What should happen next"}
                    },
                    "required": ["status", "summary"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute QA tools"""
        self.console.print(f"[cyan]🔧 {tool_name}[/cyan]")

        try:
            if tool_name == "get_pr_info":
                return await self._get_pr_info()
            elif tool_name == "analyze_integration":
                return await self._analyze_integration(tool_input["component_names"])
            elif tool_name == "report_blocker":
                return await self._report_blocker(
                    tool_input["blocker_type"],
                    tool_input["description"],
                    tool_input["fix_instructions"],
                    tool_input.get("files_to_modify", [])
                )
            elif tool_name == "run_qa_tests":
                return await self._run_qa_tests(tool_input["test_strategy"])
            elif tool_name == "finish_qa":
                return self._finish_qa(
                    tool_input["status"],
                    tool_input["summary"],
                    tool_input.get("next_steps", "")
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    async def _get_pr_info(self) -> dict[str, Any]:
        """Get PR info and previous QA state"""
        async with GitHubAPI(self.github_token) as gh:
            pr_data = await gh.get_pull_request(self.repo_ref, self.pr_number)
            files = await gh.list_pull_files(self.repo_ref, self.pr_number)

        # Check if this is a retry after fixing issues
        is_retry = len(self.state["attempts"]) > 0
        previous_blockers = self.state.get("known_issues", [])

        self.console.print(f"[green]   ✓ PR #{self.pr_number}: {pr_data['title']}[/green]")
        if is_retry:
            self.console.print(f"[yellow]   ⚠ Retry attempt {len(self.state['attempts']) + 1}[/yellow]")
            self.console.print(f"[yellow]   Previous blockers: {', '.join(previous_blockers)}[/yellow]")

        return {
            "pr_number": self.pr_number,
            "title": pr_data["title"],
            "author": pr_data["user"]["login"],
            "repo": f"{self.repo_ref.owner}/{self.repo_ref.name}",
            "changed_files": [f["filename"] for f in files],
            "is_retry": is_retry,
            "previous_blockers": previous_blockers,
            "last_status": self.state.get("last_status")
        }

    async def _analyze_integration(self, component_names: list[str]) -> dict[str, Any]:
        """Check if components are properly integrated"""
        app_jsx = self.worktree_path / "frontend" / "src" / "App.jsx"

        if not app_jsx.exists():
            return {
                "integrated": False,
                "blocker": "App.jsx not found",
                "components_checked": component_names
            }

        app_content = app_jsx.read_text()

        # Check integration
        issues = []
        has_router = "BrowserRouter" in app_content or "Routes" in app_content

        if not has_router:
            issues.append("No routing configured (missing BrowserRouter/Routes)")

        missing_imports = []
        for component in component_names:
            if component not in app_content:
                missing_imports.append(component)

        if missing_imports:
            issues.append(f"Components not imported: {', '.join(missing_imports)}")

        # Check if there are any Route components
        route_count = app_content.count("<Route")
        if route_count == 0 and missing_imports:
            issues.append("No routes defined for new components")

        is_integrated = len(issues) == 0

        self.console.print(f"[{'green' if is_integrated else 'yellow'}]   Integration: {'✓ OK' if is_integrated else '✗ Issues found'}[/{'green' if is_integrated else 'yellow'}]")
        if issues:
            for issue in issues:
                self.console.print(f"[dim]      - {issue}[/dim]")

        return {
            "integrated": is_integrated,
            "has_router": has_router,
            "route_count": route_count,
            "missing_imports": missing_imports,
            "issues": issues,
            "components_checked": component_names,
            "blocker_type": "missing_routing" if not has_router else "missing_integration"
        }

    async def _report_blocker(
        self,
        blocker_type: str,
        description: str,
        fix_instructions: str,
        files_to_modify: list[str]
    ) -> dict[str, Any]:
        """Report blocker and comment on PR"""

        # Format developer handoff
        dev_handoff = f"""## 🚫 QA Blocker Detected

**PR:** #{self.pr_number}
**Repository:** {self.repo_ref.owner}/{self.repo_ref.name}
**Blocker Type:** `{blocker_type}`

### Issue Description
{description}

### Files to Modify
{chr(10).join(f'- `{f}`' for f in files_to_modify) if files_to_modify else 'N/A'}

### Fix Instructions
{fix_instructions}

### For Developer Agent
```json
{{
  "action": "fix_blocker",
  "pr_number": {self.pr_number},
  "repository": "{self.repo_ref.owner}/{self.repo_ref.name}",
  "blocker_type": "{blocker_type}",
  "files_to_modify": {json.dumps(files_to_modify)},
  "instructions": "{fix_instructions.replace(chr(10), ' ')}"
}}
```

---
*🤖 Posted by Autonomous QA Agent*
"""

        # Save to state
        self.state["known_issues"].append(blocker_type)
        self.state["attempts"].append({
            "timestamp": "now",
            "status": "BLOCKED",
            "blocker": blocker_type
        })
        self._save_state()

        # Post comment to PR
        try:
            async with GitHubAPI(self.github_token) as gh:
                await gh.create_comment(self.repo_ref, self.pr_number, dev_handoff)
            self.console.print(f"[green]   ✓ Posted blocker comment to PR #{self.pr_number}[/green]")
        except Exception as e:
            self.console.print(f"[yellow]   ⚠ Could not post comment: {e}[/yellow]")

        # Write developer handoff file
        handoff_file = Path(f"developer_handoff_pr{self.pr_number}.md")
        handoff_file.write_text(dev_handoff)
        self.console.print(f"[green]   ✓ Wrote developer handoff: {handoff_file}[/green]")

        return {
            "blocker_reported": True,
            "pr_commented": True,
            "handoff_file": str(handoff_file),
            "dev_handoff": dev_handoff
        }

    async def _run_qa_tests(self, test_strategy: str) -> dict[str, Any]:
        """Run actual QA tests"""
        # Placeholder - would run real tests
        self.console.print(f"[cyan]   ▶ Running tests with strategy: {test_strategy}[/cyan]")
        return {
            "tests_run": True,
            "strategy": test_strategy,
            "status": "Would run tests here"
        }

    def _finish_qa(self, status: str, summary: str, next_steps: str) -> dict[str, Any]:
        """Finish QA process"""
        self.state["last_status"] = status
        self.state["attempts"].append({
            "timestamp": "now",
            "status": status,
            "summary": summary
        })
        self._save_state()

        return {
            "finished": True,
            "status": status,
            "summary": summary,
            "next_steps": next_steps
        }

    async def run(self) -> str:
        """Run smart QA agent"""
        self.console.print(Panel.fit(
            f"[bold cyan]🧠 Smart QA Agent with Memory[/bold cyan]\n"
            f"PR #{self.pr_number} @ {self.repo_ref.owner}/{self.repo_ref.name}",
            border_style="cyan"
        ))

        initial_prompt = f"""You are a SMART QA agent with memory and blocker detection.

Your workflow:
1. get_pr_info - Get PR details and check if this is a retry
   - If retry: Previous blockers will be listed
   - Check if those blockers are now fixed

2. analyze_integration - Check if new code is properly integrated
   - Look for missing routes, imports, wiring
   - Detect blockers that prevent testing

3. Decision point:
   a) If BLOCKERS found → use report_blocker
      - Post detailed issue to PR
      - Generate developer handoff with fix instructions
      - Include repo name, PR number, exact files to modify
      - Status: BLOCKED

   b) If NO blockers (or retry with fixes) → run_qa_tests
      - Generate and run tests
      - Record videos
      - Status: PASSED or FAILED

4. finish_qa - Report final status

CRITICAL RULES:
- NEVER try to test if blockers exist
- If components aren't integrated, that's a BLOCKER
- Report blockers with actionable fix instructions
- Remember previous issues and verify they're fixed on retry

Repository: {self.repo_ref.owner}/{self.repo_ref.name}
PR: #{self.pr_number}

Start by calling get_pr_info."""

        messages = [{"role": "user", "content": initial_prompt}]

        for iteration in range(8):
            self.console.print(f"\n[dim]Iteration {iteration + 1}/8[/dim]")

            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4000,
                tools=self.get_tools(),
                messages=messages
            )

            if response.stop_reason == "end_turn":
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                return final_text

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self.execute_tool(block.name, block.input)

                        if block.name == "finish_qa" and result.get("finished"):
                            return self._format_final_report(result)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })

                messages.append({"role": "user", "content": tool_results})

        return "[yellow]Agent did not complete in 8 iterations[/yellow]"

    def _format_final_report(self, finish_data: dict) -> str:
        """Format final QA report"""
        status = finish_data.get("status", "UNKNOWN")
        summary = finish_data.get("summary", "No summary")
        next_steps = finish_data.get("next_steps", "None")

        report = f"""## Smart QA Report - PR #{self.pr_number}

**Repository:** {self.repo_ref.owner}/{self.repo_ref.name}
**Status:** {status}
**Attempts:** {len(self.state['attempts'])}

### Summary
{summary}

### Next Steps
{next_steps}

### History
"""
        for i, attempt in enumerate(self.state["attempts"], 1):
            report += f"\n{i}. {attempt.get('status', 'UNKNOWN')} - {attempt.get('summary', attempt.get('blocker', 'N/A'))}"

        report += "\n\n---\n*🤖 Smart QA Agent with Memory*"
        return report


async def run_smart_qa(
    pr_number: int,
    repo_url: str,
    worktree_path: Path,
    github_token: str,
    claude_api_key: str,
    console: Optional[Console] = None
) -> str:
    """Entry point for smart QA"""
    agent = SmartQAAgent(
        pr_number=pr_number,
        repo_url=repo_url,
        worktree_path=worktree_path,
        github_token=github_token,
        claude_api_key=claude_api_key,
        console=console
    )
    return await agent.run()
