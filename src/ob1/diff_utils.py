from __future__ import annotations

import re
import subprocess
from pathlib import Path

DIFF_BLOCK_PATTERN = re.compile(r"```(?:diff)?\n(.*?)```", re.DOTALL)


def apply_unified_diff(diff_text: str, worktree: Path) -> None:
    if not diff_text or not diff_text.strip():
        raise ValueError("No diff content returned by provider")

    process = subprocess.run(  # noqa: S603
        ["git", "apply", "--whitespace=nowarn", "-"],
        input=diff_text.encode("utf-8"),
        cwd=worktree,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr.decode().strip()
        raise RuntimeError(f"Failed to apply diff: {stderr}")


def extract_diff_block(text: str) -> str | None:
    match = DIFF_BLOCK_PATTERN.search(text)
    if not match:
        return None
    diff = match.group(1).strip()
    if not diff.endswith("\n"):
        diff += "\n"
    return diff


def save_transcript(repo_root: Path, branch: str, provider: str, content: str) -> Path:
    transcripts_dir = repo_root / ".ob1" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    path = transcripts_dir / f"{branch.replace('/', '_')}_{provider}.log"
    path.write_text(content)
    return path
