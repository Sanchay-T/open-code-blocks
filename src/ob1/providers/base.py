from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class ProviderResult:
    transcript_path: Path | None
    diff_text: str | None = None


class AgentProvider(Protocol):
    name: str

    async def run(
        self,
        *,
        agent_name: str,
        branch: str,
        prompt: str,
        worktree: Path,
        repo_root: Path,
    ) -> ProviderResult:
        ...
