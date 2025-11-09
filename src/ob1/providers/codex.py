from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from rich.console import Console
from unidiff import PatchSet
from unidiff.errors import UnidiffParseError

from .base import AgentProvider, ProviderResult
from ..diff_utils import extract_diff_block, save_transcript
from ..path_filters import matches_any


class CodexProvider(AgentProvider):
    name = "codex"

    def __init__(self, api_key: str, console: Console, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._console = console
        self._model = model
        self._max_attempts = 2

    async def run(
        self,
        *,
        agent_name: str,
        branch: str,
        prompt: str,
        worktree: Path,
        repo_root: Path,
        scope_patterns: List[str],
    ) -> ProviderResult:
        base_messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt(scope_patterns)},
            {"role": "user", "content": prompt},
        ]
        retry_messages: List[Dict[str, str]] = []
        failure_reason = ""
        last_content = ""
        transcript_path: Optional[Path] = None

        for attempt in range(1, self._max_attempts + 1):
            messages = [*base_messages, *retry_messages]
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                max_tokens=1800,
                messages=messages,
            )
            last_content = response.choices[0].message.content or ""
            transcript_path = save_transcript(repo_root, branch, "codex", last_content)
            diff_text = extract_diff_block(last_content)
            if not diff_text:
                failure_reason = "response was missing a ```diff``` fenced block"
            else:
                diff_text = diff_text.replace("\r\n", "\n")
                patch = self._parse_patchset(diff_text)
                if not patch:
                    fallback_diff = self._diff_from_file_blocks(last_content, repo_root)
                    if fallback_diff:
                        diff_text = fallback_diff
                        patch = self._parse_patchset(diff_text)
                    if not patch:
                        failure_reason = failure_reason or "diff did not contain any file changes"
                        continue

                scope_issue = self._validate_scope(patch, scope_patterns)
                if scope_issue:
                    failure_reason = scope_issue
                else:
                    line_count = len(diff_text.splitlines())
                    self._console.print(
                        f"[dim cyan]{agent_name}[/dim cyan] Generated {line_count}-line diff"
                    )
                    return ProviderResult(transcript_path=transcript_path, diff_text=diff_text)

            if attempt < self._max_attempts:
                retry_prompt = self._build_retry_instruction(scope_patterns, failure_reason)
                retry_messages.append({"role": "user", "content": retry_prompt})
                self._console.print(
                    f"[dim yellow]{agent_name}[/dim yellow] Retrying ({attempt + 1}/{self._max_attempts}): {failure_reason}"
                )

        failure_msg = f"Codex failed to produce a usable diff: {failure_reason}"
        if transcript_path:
            failure_msg += f" (see transcript at {transcript_path})"
        raise RuntimeError(failure_msg)

    def _build_system_prompt(self, scope_patterns: List[str]) -> str:
        scope_note = ""
        if self._scope_guard_enabled(scope_patterns):
            patterns = ", ".join(scope_patterns)
            scope_note = (
                f" Only modify files whose POSIX paths match: {patterns}. "
                "If the task cannot be completed within that scope, explain why and stop."
            )
        return (
            "You are Codex, an AI software engineer. Return ONLY a fenced ````diff```` block describing the edits."
            " Do not modify files outside the described scope." + scope_note
        )

    def _validate_scope(self, patch: PatchSet, scope_patterns: List[str]) -> Optional[str]:
        if not self._scope_guard_enabled(scope_patterns):
            return None
        allowed_files: List[str] = []
        disallowed_files: List[str] = []
        for patched_file in patch:
            path = patched_file.path or ""
            if matches_any(path, scope_patterns):
                allowed_files.append(path)
            else:
                disallowed_files.append(path)
        if disallowed_files:
            unique = ", ".join(sorted(set(disallowed_files)))
            return f"diff touched files outside the allowed scope: {unique}"
        if not allowed_files:
            patterns = ", ".join(scope_patterns)
            return f"diff must modify at least one file matching: {patterns}"
        return None

    @staticmethod
    def _scope_guard_enabled(scope_patterns: List[str]) -> bool:
        return any(pattern and pattern != "**" for pattern in scope_patterns)

    def _build_retry_instruction(self, scope_patterns: List[str], reason: str) -> str:
        scope_clause = ""
        if self._scope_guard_enabled(scope_patterns):
            scope_clause = f" Allowed scope: {', '.join(scope_patterns)}. "

        # Provide specific guidance for diff format errors
        diff_format_help = ""
        if "did not contain any file changes" in reason or "missing a ```diff```" in reason:
            diff_format_help = """

Ensure your diff follows this EXACT format:

```diff
diff --git a/path/to/file.js b/path/to/file.js
--- a/path/to/file.js
+++ b/path/to/file.js
@@ -1,3 +1,4 @@
 existing line
+new line
 another existing line
```

Requirements:
- Use unified diff format with '---' and '+++' headers
- Include correct line counts in @@ -old_start,old_count +new_start,new_count @@
- Prefix added lines with '+'
- Prefix removed lines with '-'
- Leave context lines unmodified (no prefix or single space)
"""

        return (
            f"The previous diff could not be used because {reason}. "
            f"{scope_clause}Regenerate a valid unified diff inside a ```diff``` block and return only that diff."
            f"{diff_format_help}"
        )

    @staticmethod
    def _parse_patchset(diff_text: str) -> Optional[PatchSet]:
        try:
            patch = PatchSet(diff_text)
            return patch if patch else None
        except (UnidiffParseError, UnboundLocalError, ValueError, AttributeError):
            # UnidiffParseError: standard diff parsing error
            # UnboundLocalError: malformed diff causing internal unidiff error
            # ValueError/AttributeError: other malformed diff issues
            return None

    def _diff_from_file_blocks(self, content: str, repo_root: Path) -> Optional[str]:
        block_pattern = re.compile(
            r"^[+ ]*(?P<path>(?:[\w.-]+/)*[\w.-]+\.\w+)\s*\n[+ ]*```[a-zA-Z0-9]*\n(?P<body>.*?)(?:\n[+ ]*```)",
            re.DOTALL | re.MULTILINE,
        )
        patches: List[str] = []
        for match in block_pattern.finditer(content):
            rel_path = match.group("path").lstrip("+ ").strip()
            if not rel_path:
                continue
            raw_body = match.group("body")
            normalized_body = self._strip_diff_prefixes(raw_body)
            file_path = repo_root / rel_path
            old_text = file_path.read_text() if file_path.exists() else ""
            new_text = normalized_body
            diff_lines = difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            )
            diff = "".join(diff_lines)
            if diff.strip():
                patches.append(diff)
        if patches:
            return "\n".join(patches)
        return None

    @staticmethod
    def _strip_diff_prefixes(body: str) -> str:
        cleaned_lines = []
        for line in body.splitlines():
            if line.startswith(("+", "-")):
                cleaned_lines.append(line[1:])
            else:
                cleaned_lines.append(line)
        text = "\n".join(cleaned_lines)
        if body and not body.endswith("\n"):
            text += "\n"
        return text
