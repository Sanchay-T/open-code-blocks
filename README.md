# ob1 - Parallel AI SWE Agent Orchestrator

Parallel AI SWE orchestration CLI (`ob1`) plus supporting assets for the OB1 coding assignment.

## Repo Layout
- **This repo** – houses the Python CLI, docs, and examples.
- **Target repo (`Sanchay-T/ob1-sandbox`)** – Vite/React sandbox where agents open PRs (Stage 1 output + Stage 2 QA workflow live there).

```
docs/
  guides/          # Quick-starts, integration notes, exec summary
  research/        # Provider/API research notes
examples/          # Standalone pytest/playwright/GitHub Actions samples
src/ob1/           # CLI source
tests/             # Unit tests for guardrails/context
run_stage1.txt     # Copy/paste command that spawns 3 Claude agents
                   # (now defaults to Claude + Cursor + Codex)
```

## Quick Start
```bash
# Python env (run from repo root)
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
cp .env.example .env  # then add the keys below

# Tip: .env auto-discovery
# ob1 will look for the nearest .env (and fall back to `gh auth token`),
# so once you drop your keys into /path/to/open-code-blocks/.env you can
# run commands from any subdirectory without re-exporting secrets.
# Supported keys (see scripts/validate_keys.py):
#   CLAUDE_API_KEY        -> Claude provider
#   OPENAI_API_KEY        -> Codex provider (or CODEX_CLI_KEY)
#   CURSOR_API_KEY        -> (optional) Cursor Cloud API; CLI login also works
#   GITHUB_TOKEN          -> used to push branches + create PRs

# Claude Agent SDK prerequisites (Node CLI)
npm install -g @anthropic-ai/claude-code

# Cursor CLI prerequisite (diff mode). After install, run:
#   cursor-agent login
curl https://cursor.com/install -fsS | bash

# Diagnostics
ob1 doctor
ob1 run -m "Build a frontend login page" -k 3 --target https://github.com/Sanchay-T/ob1-sandbox.git

# Claude probe helper
ob1 claude-ping "Explain the repo" --system-prompt "You are concise."

# Run 3 agents (Claude + Cursor + Codex). This is Stage 1.
ob1 run -m "Build a responsive login page" -k 3 \
  --target https://github.com/Sanchay-T/ob1-sandbox.git \
  --base main \
  --scope "frontend/**"

# Run a specific provider mix
ob1 run -m "Build a responsive login page" -k 3 \
  --providers claude,codex \
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
- `ob1 run` – orchestrates k AI agents (Claude, Cursor, Codex by default) against a repo; clones the target if `--target` is provided.
- `ob1 qa --pr <number>` – Stage 2 QA agent; fetches PR context + Playwright logs and posts a Claude-authored review.

## Providers & Keys

| Provider | Env Variable(s)                     | Description                                    |
|----------|--------------------------------------|------------------------------------------------|
| Claude   | `CLAUDE_API_KEY`                     | Claude Agent SDK with repo-aware tool access   |
| Cursor   | *(CLI binary `cursor-agent`)*        | Runs Cursor CLI in non-interactive diff mode (falls back to Claude if missing) |
| Codex    | `OPENAI_API_KEY` or `CODEX_CLI_KEY`  | GPT‑4o Codex chat completions (diff contract)  |

## Notes
- Uses git worktrees per agent branch, then pushes and opens PRs via the GitHub API.
- Agent prompts include repo context + scope guardrails; only files matching `--scope` are allowed.
- Each Claude run stores its transcript under `.ob1/transcripts/<branch>.json` for auditability.
- `pytest` covers the scope parsing, context gathering, and change guard rails.
- Secrets loaded from `.env`; if missing, `gh auth token` is used automatically.
- `.ob1/` holds transient clones/worktrees; safe to delete between runs.
- GitHub Actions in `ob1-sandbox` installs deps, records the Playwright login video, uploads artifacts, and calls `ob1 qa` (using `CLAUDE_API_KEY` repo secret) so every PR receives an AI-authored QA review.
