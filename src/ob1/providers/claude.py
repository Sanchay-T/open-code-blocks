from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Sequence

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

    async def run(
        self,
        *,
        agent_name: str,
        branch: str,
        prompt: str,
        worktree: Path,
        repo_root: Path,
    ) -> ProviderResult:
        transcript = await self._run_query(agent_name, prompt, worktree)
        transcript_path = self._persist_transcript(repo_root, branch, transcript)
        return ProviderResult(transcript_path=transcript_path)

    async def _run_query(self, agent_name: str, prompt: str, worktree: Path) -> List[object]:
        os.environ["CLAUDE_API_KEY"] = self._api_key
        os.environ.setdefault("ANTHROPIC_API_KEY", self._api_key)
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
            raise
        return events

    def _log_event(self, agent_name: str, message: object) -> None:
        if isinstance(message, AssistantMessage):
            content_preview = []
            for block in message.content:
                if isinstance(block, TextBlock):
                    content_preview.append(block.text[:80].replace("\n", " "))
                elif isinstance(block, ToolUseBlock):
                    content_preview.append(f"tool:{block.name}")
                elif isinstance(block, ToolResultBlock):
                    content_preview.append(f"tool-result:{block.tool_name}")
            preview = " | ".join(content_preview)
            self._console.print(f"[{agent_name}] {preview}")
        else:
            self._console.print(f"[{agent_name}] {message.__class__.__name__}")

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

