from __future__ import annotations

import os
from pathlib import Path

import httpx
from rich.console import Console

from .base import AgentProvider, ProviderResult


CURSOR_API_BASE = "https://api.cursor.com/v1"


class CursorProvider(AgentProvider):
    name = "cursor"

    def __init__(self, api_key: str, console: Console) -> None:
        self._api_key = api_key
        self._console = console

    async def run(
        self,
        *,
        agent_name: str,
        branch: str,
        prompt: str,
        worktree: Path,
        repo_root: Path,
    ) -> ProviderResult:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "ob1-cursor-provider",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "mode": "diff",
            "metadata": {
                "agent": agent_name,
                "branch": branch,
            },
        }

        async with httpx.AsyncClient(base_url=CURSOR_API_BASE, timeout=180) as client:
            resp = await client.post("/agent/diff", json=payload, headers=headers)

        if resp.status_code != 200:
            raise RuntimeError(f"Cursor API error: {resp.status_code} {resp.text}")

        data = resp.json()
        diff_text = data.get("diff") or data.get("patch")
        if not diff_text:
            raise RuntimeError("Cursor response missing diff text")

        transcript_dir = repo_root / ".ob1" / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcript_dir / f"{branch.replace('/', '_')}_cursor.json"
        transcript_path.write_text(resp.text)

        self._console.print(f"[{agent_name}] Cursor returned diff with {len(diff_text.splitlines())} lines")
        return ProviderResult(transcript_path=transcript_path, diff_text=diff_text)
