from __future__ import annotations

import asyncio
import shutil
from asyncio.subprocess import PIPE
from pathlib import Path
from typing import Optional

from rich.console import Console

from .base import AgentProvider, ProviderResult
from ..diff_utils import extract_diff_block, save_transcript


class CursorProvider(AgentProvider):
    """Runs the Cursor CLI in non-interactive (print) mode to obtain a diff."""

    name = "cursor"

    def __init__(self, console: Console, cli_path: Optional[str] = None) -> None:
        self._console = console
        self._cli_path = cli_path or shutil.which("cursor-agent")
        if not self._cli_path:
            raise RuntimeError(
                "cursor-agent CLI not found. Install via `curl https://cursor.com/install -fsS | bash` or remove 'cursor'"
                " from the --providers list."
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
        prompt_payload = (
            "You are Cursor CLI running in --print mode. Respond ONLY with a fenced ```diff block describing the edits."
            " Do not add commentary outside the diff.\n\n"
            f"{prompt}"
        )
        proc = await asyncio.create_subprocess_exec(  # noqa: S603
            self._cli_path,
            "-p",
            prompt_payload,
            "--output-format",
            "text",
            cwd=str(worktree),
            stdout=PIPE,
            stderr=PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="ignore")
        stderr = stderr_bytes.decode("utf-8", errors="ignore")

        if proc.returncode != 0:
            raise RuntimeError(f"cursor-agent failed: {stderr or stdout}")

        diff_text = extract_diff_block(stdout)
        if not diff_text:
            raise RuntimeError("cursor-agent did not return a unified diff. Ensure `--output-format text` is supported.")

        transcript_path = save_transcript(repo_root, branch, "cursor", stdout)
        self._console.print(f"[{agent_name}] Cursor diff contains {len(diff_text.splitlines())} lines")
        return ProviderResult(transcript_path=transcript_path, diff_text=diff_text)
