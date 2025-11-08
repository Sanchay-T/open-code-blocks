from __future__ import annotations

from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI
from rich.console import Console

from .base import AgentProvider, ProviderResult
from ..diff_utils import extract_diff_block, save_transcript


class CodexProvider(AgentProvider):
    name = "codex"

    def __init__(self, api_key: str, console: Console, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._console = console
        self._model = model

    async def run(
        self,
        *,
        agent_name: str,
        branch: str,
        prompt: str,
        worktree: Path,
        repo_root: Path,
    ) -> ProviderResult:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Codex, an AI software engineer. Return ONLY a fenced ````diff```` block "
                    "describing the edits. Do not modify files outside the described scope."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            max_tokens=1800,
            messages=messages,
        )

        content = response.choices[0].message.content or ""
        diff_text = extract_diff_block(content)
        if not diff_text:
            raise RuntimeError("Codex response missing unified diff fenced block")

        transcript_path = save_transcript(repo_root, branch, "codex", content)

        self._console.print(f"[{agent_name}] Codex produced diff with {len(diff_text.splitlines())} lines")
        return ProviderResult(transcript_path=transcript_path, diff_text=diff_text)
