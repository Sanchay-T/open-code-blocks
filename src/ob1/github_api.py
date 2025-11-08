from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import httpx


class GitHubAPIError(RuntimeError):
    pass


def parse_github_repo(url: str) -> Tuple[str, str]:
    cleaned = url.strip()
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]

    if cleaned.startswith("git@github.com:"):
        path = cleaned.split(":", 1)[1]
    elif "github.com/" in cleaned:
        path = cleaned.split("github.com/", 1)[1]
    else:
        raise GitHubAPIError(f"Unsupported GitHub URL: {url}")

    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise GitHubAPIError(f"Cannot parse owner/repo from {url}")
    owner, repo = parts[0], parts[1]
    return owner, repo


@dataclass
class RepoRef:
    owner: str
    name: str
    origin_url: str


class GitHubAPI:
    def __init__(self, token: str, base_url: str = "https://api.github.com") -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "ob1-cli"
            },
            timeout=60.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    async def create_pull_request(
        self,
        repo: RepoRef,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
    ) -> str:
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            payload["body"] = body

        resp = await self._client.post(f"/repos/{repo.owner}/{repo.name}/pulls", json=payload)
        if resp.status_code not in {201, 202}:
            raise GitHubAPIError(f"Failed to create PR: {resp.status_code} {resp.text}")
        data = resp.json()
        return data.get("html_url") or ""

