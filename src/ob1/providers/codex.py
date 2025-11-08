from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI
from rich.console import Console

from .base import AgentProvider, ProviderResult

DIFF_BLOCK_PATTERN = re.compile(r"```(?:diff)?\n(.*?)```", re.DOTALL)


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
        diff_text = _extract_diff_block(content)
        if not diff_text:
            raise RuntimeError("Codex response missing unified diff fenced block")

        transcript_dir = repo_root / ".ob1" / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcript_dir / f"{branch.replace('/', '_')}_codex.json"
        transcript_path.write_text(content)

        self._console.print(f"[{agent_name}] Codex produced diff with {len(diff_text.splitlines())} lines")
        return ProviderResult(transcript_path=transcript_path, diff_text=diff_text)


def _extract_diff_block(text: str) -> Optional[str]:
    match = DIFF_BLOCK_PATTERN.search(text)
    if not match:
        return None
    diff = match.group(1)
    if not diff.strip().startswith("diff") and not diff.strip().startswith("---"):
        # Ensure diff header for git apply
        diff = "diff --git a/placeholder b/placeholder\n" + diff
    return diff.strip() + "\n"
