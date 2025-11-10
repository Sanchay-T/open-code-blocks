#!/usr/bin/env python3
"""
Autonomous QA Agent using Claude with Extended Thinking

This agent is given a goal: "Test features added in PR #X"
It has tools available and reasons through how to accomplish the goal.

NO hardcoded logic - the agent figures out its own strategy.
"""
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Optional
from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ob1.github_api import GitHubAPI, RepoRef, parse_github_repo


class AutonomousQAAgent:
    """Autonomous QA agent that reasons and acts using Claude"""

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

        # Parse repo info
        owner, repo_name = parse_github_repo(repo_url)
        self.repo_ref = RepoRef(owner=owner, name=repo_name, origin_url=repo_url)

        # Conversation history for agentic loop
        self.messages = []

    def get_tools(self) -> list[dict]:
        """Define tools available to the agent"""
        return [
            {
                "name": "analyze_pr",
                "description": "Fetch PR metadata, changed files, and diffs from GitHub. Returns PR title, description, author, changed files with their diffs.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "read_file",
                "description": "Read a file from the worktree (the checked-out PR branch). Use this to examine source code, config files, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file relative to worktree root (e.g., 'frontend/src/App.jsx')"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Create or overwrite a file in the worktree. Use this to create test files, test harnesses, or modify existing files.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file relative to worktree root"
                        },
                        "content": {
                            "type": "string",
                            "description": "Full content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "run_command",
                "description": "Execute a shell command in the worktree directory. Use for npm install, running tests, building, etc. Returns stdout, stderr, and exit code.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory relative to worktree root (optional)"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 120)"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "analyze_screenshot",
                "description": "Use Claude Vision to analyze a screenshot and verify what's displayed. Returns description of what's shown in the image.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to screenshot file relative to worktree root"
                        },
                        "question": {
                            "type": "string",
                            "description": "What to analyze (e.g., 'What component is displayed?', 'Is this a dashboard or login screen?')"
                        }
                    },
                    "required": ["image_path", "question"]
                }
            },
            {
                "name": "list_files",
                "description": "List files in a directory in the worktree. Use to explore directory structure.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path relative to worktree root (default: '.')"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to filter files (e.g., '*.jsx', '**/*.spec.ts')"
                        }
                    },
                    "required": []
                }
            }
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute a tool and return results"""
        self.console.print(f"[cyan]🔧 Tool: {tool_name}[/cyan]")
        self.console.print(f"[dim]   Input: {json.dumps(tool_input, indent=2)}[/dim]")

        try:
            if tool_name == "analyze_pr":
                return await self._analyze_pr()
            elif tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "write_file":
                return self._write_file(tool_input["path"], tool_input["content"])
            elif tool_name == "run_command":
                return self._run_command(
                    tool_input["command"],
                    tool_input.get("cwd"),
                    tool_input.get("timeout", 120)
                )
            elif tool_name == "analyze_screenshot":
                return await self._analyze_screenshot(
                    tool_input["image_path"],
                    tool_input["question"]
                )
            elif tool_name == "list_files":
                return self._list_files(
                    tool_input.get("path", "."),
                    tool_input.get("pattern")
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_pr(self) -> dict[str, Any]:
        """Fetch PR metadata and changes from GitHub"""
        async with GitHubAPI(self.github_token) as gh:
            pr_data = await gh.get_pull_request(self.repo_ref, self.pr_number)
            files = await gh.list_pull_files(self.repo_ref, self.pr_number)

        # Extract relevant info
        result = {
            "title": pr_data["title"],
            "description": pr_data.get("body", ""),
            "author": pr_data["user"]["login"],
            "state": pr_data["state"],
            "changed_files": []
        }

        for f in files:
            file_info = {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "patch": f.get("patch", "")
            }
            result["changed_files"].append(file_info)

        self.console.print(f"[green]   ✓ Found {len(files)} changed files[/green]")
        return result

    def _read_file(self, path: str) -> dict[str, Any]:
        """Read file from worktree"""
        file_path = self.worktree_path / path
        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        try:
            content = file_path.read_text()
            self.console.print(f"[green]   ✓ Read {len(content)} chars from {path}[/green]")
            return {"content": content, "path": path}
        except Exception as e:
            return {"error": f"Failed to read {path}: {e}"}

    def _write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write file to worktree"""
        file_path = self.worktree_path / path

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            self.console.print(f"[green]   ✓ Wrote {len(content)} chars to {path}[/green]")
            return {"success": True, "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"error": f"Failed to write {path}: {e}"}

    def _run_command(self, command: str, cwd: Optional[str], timeout: int) -> dict[str, Any]:
        """Execute shell command"""
        work_dir = self.worktree_path / cwd if cwd else self.worktree_path

        self.console.print(f"[cyan]   ▶ Running: {command}[/cyan]")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            status = "✓" if result.returncode == 0 else "✗"
            self.console.print(f"[{'green' if result.returncode == 0 else 'yellow'}]   {status} Exit code: {result.returncode}[/{'green' if result.returncode == 0 else 'yellow'}]")

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_screenshot(self, image_path: str, question: str) -> dict[str, Any]:
        """Use Claude Vision to analyze screenshot"""
        file_path = self.worktree_path / image_path

        if not file_path.exists():
            return {"error": f"Screenshot not found: {image_path}"}

        try:
            import base64

            # Read and encode image
            image_data = base64.standard_b64encode(file_path.read_bytes()).decode("utf-8")

            # Determine media type
            suffix = file_path.suffix.lower()
            media_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif"
            }
            media_type = media_type_map.get(suffix, "image/png")

            # Call Claude Vision
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }]
            )

            analysis = response.content[0].text
            self.console.print(f"[green]   ✓ Analyzed screenshot[/green]")
            return {"analysis": analysis}

        except Exception as e:
            return {"error": f"Failed to analyze screenshot: {e}"}

    def _list_files(self, path: str, pattern: Optional[str]) -> dict[str, Any]:
        """List files in directory"""
        dir_path = self.worktree_path / path

        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}

        try:
            if pattern:
                files = [str(f.relative_to(self.worktree_path)) for f in dir_path.glob(pattern)]
            else:
                files = [str(f.relative_to(self.worktree_path)) for f in dir_path.iterdir()]

            self.console.print(f"[green]   ✓ Found {len(files)} files[/green]")
            return {"files": files, "count": len(files)}
        except Exception as e:
            return {"error": str(e)}

    async def run(self, max_iterations: int = 20) -> str:
        """Run the autonomous agent loop"""

        self.console.print(Panel.fit(
            f"[bold cyan]🤖 Autonomous QA Agent[/bold cyan]\n"
            f"PR #{self.pr_number} @ {self.repo_url}\n"
            f"Worktree: {self.worktree_path}",
            border_style="cyan"
        ))

        # Initial goal/prompt for the agent
        initial_prompt = f"""You are an autonomous QA testing agent. Your goal:

**Test the features added in PR #{self.pr_number}**

Your job:
1. Understand what was added in this PR
2. Figure out how to test it (even if the features aren't integrated into the main app yet)
3. Generate Playwright tests that demonstrate the NEW features
4. Run the tests and ensure they record videos showing the actual new features
5. Verify the videos show the correct features (not unrelated screens)
6. Generate a comprehensive QA report

You have access to tools:
- analyze_pr: Fetch PR changes
- read_file: Read files from the worktree
- write_file: Create/modify files
- run_command: Execute shell commands
- analyze_screenshot: Use vision to verify screenshots
- list_files: Explore directory structure

Important guidelines:
- If new components aren't integrated into the main app, CREATE a test harness to render them
- Don't just test the homepage - test what was ADDED in the PR
- Use your reasoning to figure out the best strategy
- Be creative and autonomous - there's no hardcoded solution

The worktree is at: {self.worktree_path}
The frontend code is likely in: frontend/src/

Begin by analyzing the PR to understand what was added."""

        self.messages.append({
            "role": "user",
            "content": initial_prompt
        })

        # Agentic loop
        for iteration in range(max_iterations):
            self.console.print(f"\n[bold magenta]{'='*60}[/bold magenta]")
            self.console.print(f"[bold magenta]Iteration {iteration + 1}/{max_iterations}[/bold magenta]")
            self.console.print(f"[bold magenta]{'='*60}[/bold magenta]\n")

            # Call Claude with extended thinking
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Latest model with extended thinking
                max_tokens=16000,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 10000
                },
                tools=self.get_tools(),
                messages=self.messages
            )

            # Display thinking if present
            for block in response.content:
                if block.type == "thinking":
                    self.console.print(Panel(
                        block.thinking[:500] + "..." if len(block.thinking) > 500 else block.thinking,
                        title="[bold yellow]🧠 Agent Thinking[/bold yellow]",
                        border_style="yellow"
                    ))

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Agent is done - extract final response
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text

                self.console.print(Panel(
                    final_text,
                    title="[bold green]✅ Agent Complete[/bold green]",
                    border_style="green"
                ))

                return final_text

            # Handle tool use
            if response.stop_reason == "tool_use":
                # Add assistant response to history
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute all tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self.execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, indent=2)
                        })

                # Add tool results to history
                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })

            elif response.stop_reason == "max_tokens":
                self.console.print("[yellow]⚠ Agent hit max tokens, continuing...[/yellow]")
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                self.messages.append({
                    "role": "user",
                    "content": "Continue where you left off."
                })

        return "[red]Agent exceeded maximum iterations[/red]"


async def run_autonomous_qa(
    pr_number: int,
    repo_url: str,
    worktree_path: Path,
    github_token: str,
    claude_api_key: str,
    console: Optional[Console] = None
) -> str:
    """Entry point for autonomous QA"""
    agent = AutonomousQAAgent(
        pr_number=pr_number,
        repo_url=repo_url,
        worktree_path=worktree_path,
        github_token=github_token,
        claude_api_key=claude_api_key,
        console=console
    )

    return await agent.run()
