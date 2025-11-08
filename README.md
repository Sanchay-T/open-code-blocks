# open-code-blocks

Parallel AI SWE orchestration CLI (`ob1`) plus supporting assets for the OB1 coding assignment.

## Repo Layout
- **This repo** – houses the Python CLI, scripts, docs.
- **Target repo (`Sanchay-T/ob1-sandbox`)** – Vite/React sandbox where agents open PRs.

## Quick Start
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env  # then add GITHUB_TOKEN, CLAUDE_API_KEY, etc.

ob1 doctor
ob1 run -m "Build a frontend login page" -k 3 --target https://github.com/Sanchay-T/ob1-sandbox.git
```

## Commands
- `ob1 doctor` – validates git repo + remotes.
- `ob1 mkworktree <branch>` – helper for manual worktree creation.
- `ob1 run` – orchestrates k agents (currently trivial diff creator) against a repo; clones the target if `--target` is provided.

## Notes
- Uses git worktrees per agent branch, then pushes and opens PRs via the GitHub API.
- Secrets loaded from `.env` via `pydantic-settings` (never committed).
- `.ob1/` holds transient clones/worktrees; safe to delete between runs.
