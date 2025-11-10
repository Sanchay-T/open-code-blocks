from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Sequence, Dict, Any
from collections import defaultdict

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    query,
)
from rich.console import Console

from ..providers.base import AgentProvider, ProviderResult


class ClaudeProvider(AgentProvider):
    def __init__(
        self,
        *,
        api_key: str,
        console: Console,
        allowed_tools: Sequence[str] | None = None,
        permission_mode: str = "acceptEdits",
        system_prompt: str | None = None,
    ) -> None:
        self.name = "claude"
        self._api_key = api_key
        self._console = console
        self._allowed_tools = list(allowed_tools or [])
        self._permission_mode = permission_mode
        self._system_prompt = system_prompt or (
            "You are ob1, an elite frontend engineer who produces production-ready React code quickly."
        )
        # Activity tracking for cleaner output
        self._activity_tracker: Dict[str, Dict[str, Any]] = {}

    async def run(
        self,
        *,
        agent_name: str,
        branch: str,
        prompt: str,
        worktree: Path,
        repo_root: Path,
        scope_patterns: list[str],
    ) -> ProviderResult:
        transcript: List[object] = []
        try:
            transcript = await self._run_query(agent_name, prompt, worktree)
        except Exception as exc:  # noqa: BLE001
            events = transcript or getattr(exc, "_ob1_events", [])
            if events:
                self._persist_transcript(repo_root, branch, events)
            raise

        transcript_path = self._persist_transcript(repo_root, branch, transcript)
        return ProviderResult(transcript_path=transcript_path)

    async def _run_query(self, agent_name: str, prompt: str, worktree: Path) -> List[object]:
        os.environ["CLAUDE_API_KEY"] = self._api_key
        os.environ["ANTHROPIC_API_KEY"] = self._api_key
        options = ClaudeAgentOptions(
            allowed_tools=self._allowed_tools or None,
            permission_mode=self._permission_mode,
            cwd=str(worktree),
            system_prompt=self._system_prompt,
            setting_sources=["project", "user"],
        )

        events: List[object] = []
        try:
            async for message in query(prompt=prompt, options=options):
                events.append(message)
                self._log_event(agent_name, message)
        except ClaudeSDKError as exc:
            self._console.print(f"[red]Claude SDK error ({agent_name}):[/red] {exc}")
            setattr(exc, "_ob1_events", events)
            raise
        except Exception as exc:  # noqa: BLE001
            setattr(exc, "_ob1_events", events)
            raise
        return events

    def _log_event(self, agent_name: str, message: object) -> None:
        """Smart event logging - filters spam, groups activities, shows progress."""
        # FILTER OUT internal SDK messages (SystemMessage, UserMessage, ResultMessage)
        # These are implementation details, not user-relevant information
        if not isinstance(message, AssistantMessage):
            return

        # Track activity for this agent
        if agent_name not in self._activity_tracker:
            self._activity_tracker[agent_name] = {
                'phase': '🔍 Discovery',
                'tools_used': [],
                'last_update_count': 0,
            }

        tracker = self._activity_tracker[agent_name]

        # Process AssistantMessage blocks
        for block in message.content:
            if isinstance(block, ToolUseBlock):
                # Track tool usage and update phase
                tracker['tools_used'].append(block.name)

                # Determine phase based on tool patterns
                if block.name in ('Read', 'Glob', 'Grep'):
                    if tracker['phase'] != '🔍 Discovery':
                        tracker['phase'] = '🔍 Discovery'
                elif block.name in ('Write', 'Edit'):
                    if tracker['phase'] != '✏️  Implementation':
                        tracker['phase'] = '✏️  Implementation'
                        self._console.print(f"[dim cyan]{agent_name}[/dim cyan] → {tracker['phase']}")
                elif block.name == 'Bash':
                    # Check if it's a build/test command
                    if tracker['phase'] != '🧪 Verification':
                        tracker['phase'] = '🧪 Verification'
                        self._console.print(f"[dim cyan]{agent_name}[/dim cyan] → {tracker['phase']}")

                # Show condensed updates every 5 tools (not every single one)
                tool_count = len(tracker['tools_used'])
                if tool_count % 5 == 0 and tool_count != tracker['last_update_count']:
                    self._console.print(
                        f"[dim]{agent_name}[/dim] {tracker['phase']} "
                        f"[dim]({tool_count} actions)[/dim]"
                    )
                    tracker['last_update_count'] = tool_count

            elif isinstance(block, TextBlock) and block.text.strip():
                # Only log significant text blocks (> 50 chars), skip truncation
                text = block.text.strip()
                if len(text) > 50:
                    # Show first meaningful sentence without truncation
                    first_line = text.splitlines()[0]
                    if len(first_line) > 200:
                        # Only truncate if REALLY long
                        first_line = first_line[:200] + "..."
                    self._console.print(f"[dim cyan]{agent_name}[/dim cyan] {first_line}")

    def _persist_transcript(self, repo_root: Path, branch: str, events: Sequence[object]) -> Path:
        transcripts_dir = repo_root / ".ob1" / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        path = transcripts_dir / f"{branch.replace('/', '_')}.json"
        payload = [self._serialize_event(event) for event in events]
        path.write_text(json.dumps(payload, indent=2))
        return path

    def _serialize_event(self, event: object) -> dict:
        if hasattr(event, "__dataclass_fields__"):
            return asdict(event)
        if isinstance(event, SystemMessage):
            return asdict(event)
        return {"repr": repr(event)}
