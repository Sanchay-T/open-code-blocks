from __future__ import annotations

import asyncio
import shutil
import re
from asyncio.subprocess import PIPE
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console

from .base import AgentProvider, ProviderResult
from ..diff_utils import extract_diff_block, save_transcript
from ..git_ops import run_git


_HUNK_HEADER_RE = re.compile(r"@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@")


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
        scope_patterns: list[str],
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

        transcript_path = save_transcript(repo_root, branch, "cursor", stdout)
        status = run_git("status", "--porcelain", cwd=worktree)
        if status.strip():
            diff_output = run_git("diff", cwd=worktree)
            file_count = len([line for line in status.splitlines() if line.strip()])
            self._console.print(
                f"[dim cyan]{agent_name}[/dim cyan] Modified {file_count} file(s)"
            )
            return ProviderResult(
                transcript_path=transcript_path,
                diff_text=diff_output,
            )

        diff_text = extract_diff_block(stdout)
        if not diff_text:
            raise RuntimeError(
                "cursor-agent did not return a unified diff and no file changes were detected. "
                "Ensure `--output-format text` is supported."
            )

        sanitized_diff, dropped_blocks = _sanitize_cursor_diff(diff_text, worktree)
        # Only show warnings if blocks were dropped (less noise)
        if dropped_blocks:
            self._console.print(
                f"[dim yellow]{agent_name}[/dim yellow] Sanitized diff ({len(dropped_blocks)} invalid blocks dropped)"
            )
        if not sanitized_diff.strip():
            raise RuntimeError("cursor-agent produced diff output, but no valid hunks remained after sanitization.")

        line_count = len(sanitized_diff.splitlines())
        self._console.print(f"[dim cyan]{agent_name}[/dim cyan] Generated {line_count}-line diff")
        return ProviderResult(transcript_path=transcript_path, diff_text=sanitized_diff)


def _sanitize_cursor_diff(diff_text: str, worktree: Path) -> Tuple[str, List[str]]:
    """Normalize cursor diff output by enforcing LF endings and dropping incomplete hunks."""

    normalized = diff_text.replace("\r\n", "\n").strip("\n")
    if not normalized:
        return "", []

    blocks = _split_diff_blocks(normalized)
    valid_blocks: List[str] = []
    dropped_blocks: List[str] = []

    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        block = _ensure_diff_header(block, worktree)
        block = _normalize_hunk_lines(block)
        if _looks_like_patch(block):
            valid_blocks.append(block.rstrip("\n"))
        else:
            dropped_blocks.append(block)

    if not valid_blocks:
        return "", dropped_blocks

    sanitized = "\n\n".join(valid_blocks) + "\n"
    return sanitized, dropped_blocks


def _split_diff_blocks(diff_text: str) -> List[str]:
    lines = diff_text.splitlines()
    blocks: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if line.startswith("diff --git "):
            if current:
                blocks.append(current)
                current = []
        current.append(line)
    if current:
        blocks.append(current)
    return ["\n".join(block) for block in blocks]


def _ensure_diff_header(block: str, worktree: Path) -> str:
    stripped = block.lstrip()
    if stripped.startswith("diff --git "):
        # Rewrite header to guarantee a/b prefixes even if they already exist.
        old_path = _extract_path(block, "--- ")
        new_path = _extract_path(block, "+++ ")
        if old_path and new_path:
            header = _build_header(old_path, new_path, worktree)
            # Replace existing header with normalized one
            lines = block.splitlines()
            lines[0] = header
            return "\n".join(lines)
        return block
    old_path = _extract_path(block, "--- ")
    new_path = _extract_path(block, "+++ ")
    if old_path and new_path:
        header = _build_header(old_path, new_path, worktree)
        return f"{header}\n{block}"
    return block


def _normalize_hunk_lines(block: str) -> str:
    """Ensure each hunk line uses an explicit diff prefix and accurate counts."""

    lines = block.splitlines()
    normalized: List[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if _HUNK_HEADER_RE.match(line):
            header = line
            idx += 1
            body: List[str] = []
            while idx < len(lines) and not _HUNK_HEADER_RE.match(lines[idx]) and not lines[idx].startswith("diff --git "):
                body.append(lines[idx])
                idx += 1
            fixed_header, fixed_body = _rewrite_hunk(header, body)
            normalized.append(fixed_header)
            normalized.extend(fixed_body)
            continue
        normalized.append(line)
        idx += 1
    return "\n".join(normalized)


def _rewrite_hunk(header: str, body: List[str]) -> Tuple[str, List[str]]:
    normalized_body: List[str] = []
    for line in body:
        if line.startswith(("diff --git ", "index ", "--- ", "+++ ")):
            normalized_body.append(line)
            continue
        if line.startswith(("+", "-", " ")) or line.startswith("\\"):
            normalized_body.append(line)
        else:
            normalized_body.append(" " + line)

    match = _HUNK_HEADER_RE.match(header)
    if not match:
        return header, normalized_body

    old_start = match.group("old_start")
    new_start = match.group("new_start")
    old_line_count = sum(1 for line in normalized_body if line.startswith((" ", "-")))
    new_line_count = sum(1 for line in normalized_body if line.startswith((" ", "+")))

    header = f"@@ -{_format_range(old_start, old_line_count)} +{_format_range(new_start, new_line_count)} @@"
    return header, normalized_body


def _format_range(start: str, count: int) -> str:
    if count == 1:
        return start
    return f"{start},{count}"


def _build_header(old_path: str, new_path: str, worktree: Path) -> str:
    left_rel = _clean_path(old_path, worktree)
    right_rel = _clean_path(new_path, worktree)
    if left_rel == "dev/null":
        left_rel = right_rel
    if right_rel == "dev/null":
        right_rel = left_rel
    left = f"a/{left_rel}"
    right = f"b/{right_rel}"
    return f"diff --git {left} {right}"


def _clean_path(raw_path: str, worktree: Path) -> str:
    path = raw_path.strip()
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    if path.startswith("./"):
        path = path[2:]
    path = path.replace("\\", "/")
    if path.startswith("/"):
        try:
            rel = Path(path).relative_to(worktree)
            path = rel.as_posix()
        except ValueError:
            path = path.lstrip("/")
    return path or "unknown-path"


def _extract_path(block: str, prefix: str) -> Optional[str]:
    for line in block.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _looks_like_patch(block: str) -> bool:
    has_old = False
    has_new = False
    has_hunk = False
    for line in block.splitlines():
        if line.startswith("--- "):
            has_old = True
        elif line.startswith("+++ "):
            has_new = True
        elif line.startswith("@@"):
            has_hunk = True
        if has_old and has_new and has_hunk:
            return True
    return False
