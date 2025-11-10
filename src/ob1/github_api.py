from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

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

    async def post_comment(self, repo: RepoRef, issue_number: int, body: str) -> None:
        payload = {"body": body}
        resp = await self._client.post(
            f"/repos/{repo.owner}/{repo.name}/issues/{issue_number}/comments", json=payload
        )
        if resp.status_code not in {201, 200}:
            raise GitHubAPIError(f"Failed to post comment: {resp.status_code} {resp.text}")

    async def get_pull_request(self, repo: RepoRef, number: int) -> dict[str, Any]:
        resp = await self._client.get(f"/repos/{repo.owner}/{repo.name}/pulls/{number}")
        if resp.status_code != 200:
            raise GitHubAPIError(f"Failed to fetch PR #{number}: {resp.status_code} {resp.text}")
        return resp.json()

    async def list_pull_files(self, repo: RepoRef, number: int) -> List[dict[str, Any]]:
        files: List[dict[str, Any]] = []
        page = 1
        while True:
            resp = await self._client.get(
                f"/repos/{repo.owner}/{repo.name}/pulls/{number}/files", params={"page": page, "per_page": 100}
            )
            if resp.status_code != 200:
                raise GitHubAPIError(f"Failed to list PR files: {resp.status_code} {resp.text}")
            chunk = resp.json()
            if not chunk:
                break
            files.extend(chunk)
            page += 1
        return files

    async def create_comment(self, repo: RepoRef, pr_number: int, body: str) -> dict[str, Any]:
        """Create a comment on a pull request"""
        resp = await self._client.post(
            f"/repos/{repo.owner}/{repo.name}/issues/{pr_number}/comments",
            json={"body": body}
        )
        if resp.status_code != 201:
            raise GitHubAPIError(f"Failed to create comment: {resp.status_code} {resp.text}")
        return resp.json()

    async def get_file_content(self, repo: RepoRef, path: str, ref: str = "HEAD") -> Optional[str]:
        """
        Fetch the contents of a file from the repository

        Args:
            repo: Repository reference
            path: Path to the file in the repository
            ref: Git ref (branch, tag, or commit SHA) to fetch from

        Returns:
            File content as string, or None if file not found
        """
        import base64

        resp = await self._client.get(
            f"/repos/{repo.owner}/{repo.name}/contents/{path}",
            params={"ref": ref}
        )

        if resp.status_code == 404:
            return None
        elif resp.status_code != 200:
            raise GitHubAPIError(f"Failed to fetch file content: {resp.status_code} {resp.text}")

        data = resp.json()
        if data.get("type") != "file":
            return None

        # Decode base64 content
        content_b64 = data.get("content", "")
        try:
            content = base64.b64decode(content_b64).decode("utf-8")
            return content
        except Exception as e:
            raise GitHubAPIError(f"Failed to decode file content: {e}")
