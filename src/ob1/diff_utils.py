from __future__ import annotations

import subprocess
from pathlib import Path


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
