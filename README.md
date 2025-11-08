# open-code-blocks

Parallel AI SWE orchestration CLI (`ob1`) plus supporting assets for the OB1 coding assignment.

## Repo Layout
- **This repo** – houses the Python CLI, scripts, docs.
- **Target repo (`Sanchay-T/ob1-sandbox`)** – Vite/React sandbox where agents open PRs.

## Quick Start
```bash
# Python env
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env  # then add GITHUB_TOKEN, CLAUDE_API_KEY, etc.

# Claude Agent SDK prerequisites (Node CLI)
npm install -g @anthropic-ai/claude-code

# Diagnostics
ob1 doctor
ob1 run -m "Build a frontend login page" -k 3 --target https://github.com/Sanchay-T/ob1-sandbox.git

# Claude probe helper
ob1 claude-ping "Explain the repo" --system-prompt "You are concise."

# Run 3 Claude agents against the sandbox repo
ob1 run -m "Build a responsive login page" -k 3 \
  --target https://github.com/Sanchay-T/ob1-sandbox.git \
  --base main \
  --scope "frontend/**"

# Run unit tests
pytest
```

## Commands
- `ob1 doctor` – validates git repo + remotes.
- `ob1 mkworktree <branch>` – helper for manual worktree creation.
- `ob1 claude-ping` – send a single prompt to Claude Agent SDK and inspect the JSON transcript.
- `ob1 run` – orchestrates k Claude agents against a repo; clones the target if `--target` is provided.
- `ob1 qa --pr <number>` – Stage 2 QA agent; fetches PR context + Playwright logs and posts a Claude-authored review.

## Notes
- Uses git worktrees per agent branch, then pushes and opens PRs via the GitHub API.
- Agent prompts include repo context + scope guardrails; only files matching `--scope` are allowed.
- Each Claude run stores its transcript under `.ob1/transcripts/<branch>.json` for auditability.
- `pytest` covers the scope parsing, context gathering, and change guard rails.
- Secrets loaded from `.env` via `pydantic-settings` (never committed).
- `.ob1/` holds transient clones/worktrees; safe to delete between runs.

## Notes
- Uses git worktrees per agent branch, then pushes and opens PRs via the GitHub API.
- Secrets loaded from `.env` via `pydantic-settings` (never committed).
- `.ob1/` holds transient clones/worktrees; safe to delete between runs.
