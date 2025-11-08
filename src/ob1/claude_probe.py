from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)
from rich.console import Console
from rich.syntax import Syntax

from .settings import get_settings


class ClaudeProbeError(RuntimeError):
    """Raised when the Claude probe cannot run."""


async def run_claude_probe(
    prompt: str,
    allowed_tools: Sequence[str],
    permission_mode: str,
    cwd: Optional[Path],
    system_prompt: Optional[str],
    env_file: Optional[Path],
) -> List[object]:
    settings = get_settings(env_file)
    api_key = settings.claude_api_key
    if not api_key:
        raise ClaudeProbeError("CLAUDE_API_KEY is not set. Add it to .env or pass --env-file")

    # The SDK checks CLAUDE_API_KEY/ANTHROPIC_API_KEY when spawning the CLI.
    os.environ.setdefault("CLAUDE_API_KEY", api_key)
    os.environ.setdefault("ANTHROPIC_API_KEY", api_key)

    options = ClaudeAgentOptions(
        allowed_tools=list(allowed_tools),
        permission_mode=permission_mode,
        cwd=str(cwd) if cwd else None,
        system_prompt=system_prompt,
    )

    events: List[object] = []
    async for message in query(prompt=prompt, options=options):
        events.append(message)
    return events


def render_transcript(events: Sequence[object], console: Console) -> None:
    for idx, message in enumerate(events, start=1):
        title = f"Message {idx}: {message.__class__.__name__}"
        console.rule(title)
        payload = _message_payload(message)
        console.print(Syntax(payload, "json", word_wrap=False, indent_guides=True))


def _message_payload(message: object) -> str:
    if isinstance(message, AssistantMessage):
        return _assistant_payload(message)
    if isinstance(message, (SystemMessage, UserMessage, ResultMessage)):
        return json.dumps(asdict(message), indent=2)
    if is_dataclass(message):
        return json.dumps(asdict(message), indent=2)
    try:
        return json.dumps(message, indent=2, default=str)
    except TypeError:
        return str(message)


def _assistant_payload(message: AssistantMessage) -> str:
    blocks = []
    for block in message.content:
        if isinstance(block, TextBlock):
            blocks.append({"type": "text", "text": block.text})
        elif isinstance(block, ToolUseBlock):
            blocks.append({"type": "tool_use", "tool": block.name, "input": block.input})
        elif isinstance(block, ToolResultBlock):
            blocks.append({"type": "tool_result", "tool": block.tool_name, "result": block.result})
        else:
            blocks.append({"type": block.__class__.__name__, **asdict(block)})
    payload = {
        "model": message.model,
        "parent_tool_use_id": message.parent_tool_use_id,
        "content": blocks,
    }
    return json.dumps(payload, indent=2)


def claude_ping(
    prompt: str,
    allowed_tools: Sequence[str],
    permission_mode: str,
    cwd: Optional[Path],
    system_prompt: Optional[str],
    env_file: Optional[Path],
    console: Console,
) -> None:
    try:
        events = asyncio.run(
            run_claude_probe(
                prompt=prompt,
                allowed_tools=allowed_tools,
                permission_mode=permission_mode,
                cwd=cwd,
                system_prompt=system_prompt,
                env_file=env_file,
            )
        )
    except ClaudeProbeError as exc:
        console.print(f"[red]Claude probe aborted:[/red] {exc}")
        raise
    except ClaudeSDKError as exc:
        console.print(f"[red]Claude SDK error:[/red] {exc}")
        raise

    render_transcript(events, console)

