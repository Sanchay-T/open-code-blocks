from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKError, TextBlock, query
from rich.console import Console

from .github_api import GitHubAPI, RepoRef, GitHubAPIError, parse_github_repo
from .settings import get_settings


@dataclass
class QAReviewConfig:
    pr_number: int
    repo_url: Optional[str]
    build_log: Optional[Path]
    test_log: Optional[Path]
    artifact_note: str
    env_file: Optional[Path]
    dry_run: bool = False


def run_qa_review(config: QAReviewConfig, console: Optional[Console] = None) -> None:
    console = console or Console()
    asyncio.run(_run_async(config, console))


async def _run_async(config: QAReviewConfig, console: Console) -> None:
    settings = get_settings(config.env_file)
    if not settings.github_token:
        raise RuntimeError("GITHUB_TOKEN must be set to run QA review")
    if not settings.claude_api_key:
        raise RuntimeError("CLAUDE_API_KEY must be set to run QA review")

    repo_url = config.repo_url
    if not repo_url:
        repo_url = _infer_origin_url()

    owner, name = parse_github_repo(repo_url)
    repo_ref = RepoRef(owner=owner, name=name, origin_url=repo_url)

    async with GitHubAPI(settings.github_token) as gh:
        pr = await gh.get_pull_request(repo_ref, config.pr_number)
        files = await gh.list_pull_files(repo_ref, config.pr_number)

    prompt = _render_prompt(
        pr=pr,
        files=files,
        build_log=_read_tail(config.build_log),
        test_log=_read_tail(config.test_log),
        artifact_note=config.artifact_note,
    )

    review_body = await _generate_review(prompt, settings.claude_api_key)
    console.print("[green]QA review generated via Claude.[/green]")
    if config.dry_run:
        console.print(review_body)
        return

    async with GitHubAPI(settings.github_token) as gh:
        await gh.post_comment(repo_ref, config.pr_number, review_body)
    console.print(f"[cyan]Posted QA review on PR #{config.pr_number}.[/cyan]")


def _infer_origin_url() -> str:
    from .git_ops import get_origin_url

    return get_origin_url()


def _read_tail(path: Optional[Path], max_chars: int = 6000) -> str:
    if not path:
        return ""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _render_prompt(pr: dict, files: list, build_log: str, test_log: str, artifact_note: str) -> str:
    files_summary = "\n".join(
        f"- {f.get('filename')} (+{f.get('additions')}/-{f.get('deletions')})" for f in files[:30]
    )
    return f"""
You are OB1 QA, an elite frontend reviewer. A teammate submitted PR #{pr.get('number')}:

Title: {pr.get('title')}
Author: {pr.get('user', {}).get('login')}

Description:
{pr.get('body') or '(no description)'}

Changed files:
{files_summary}

Continuous Integration ran `npm run build` then Playwright tests that fill the login form.

Build log tail:
```
{build_log or 'n/a'}
```

Playwright log tail:
```
{test_log or 'n/a'}
```

Artifacts available to the author: {artifact_note}.

Please review this PR:
1. Summarize what the PR appears to do.
2. Report the QA status (pass/fail) based on the logs.
3. List any blocking issues or regressions to fix.
4. Highlight UX or polish wins.

Respond in concise markdown with headers.
""".strip()


async def _generate_review(prompt: str, api_key: str) -> str:
    os.environ["CLAUDE_API_KEY"] = api_key
    os.environ.setdefault("ANTHROPIC_API_KEY", api_key)
    options = ClaudeAgentOptions(
        allowed_tools=None,
        permission_mode="default",
        system_prompt="You are an empathetic but exacting QA engineer.",
    )

    chunks: list[str] = []
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)
    except ClaudeSDKError as exc:
        raise RuntimeError(f"Claude QA review failed: {exc}") from exc
    return "\n".join(chunks).strip()
