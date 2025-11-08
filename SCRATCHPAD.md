# OB1 Scratchpad

Free-form notes, decisions, and open questions while building the orchestrator.

## Claude Agent SDK Notes
- SDK renamed to **Claude Agent SDK** (ex-Claude Code SDK).
- Python package: `claude-agent-sdk`; provides `query()` helper for single prompts and `ClaudeSDKClient` for multi-turn/tooling workflows.
- Supports MCP tools; we can expose custom apply-patch/test commands later.
- Auth strictly via `CLAUDE_API_KEY` (no piggybacking on Claude desktop login).

## Stage 1 (done / next)
- ✅ Repo cloning + worktree per agent + PR creation (trivial change placeholder).
- 🚧 Swap placeholder with real Claude-generated diffs scoped to `frontend/**`.
  - Need deterministic prompt template (context engine input, diff-only output contract).
  - Implement diff validator + apply patch + fallback.

### 2025-11-08 Claude Probe
- Installed global CLI `@anthropic-ai/claude-code` and Python dep `claude-agent-sdk`.
- Added `ob1 claude-ping` helper; command example:
  ```bash
  ob1 claude-ping "Explain what ob1 CLI currently does" --system-prompt "You are a concise technical writer."
  ```
- Output shows the raw SystemMessage + AssistantMessage JSON, including tool availability and model (`claude-sonnet-4-5-20250929`).
- Next: allow optional tool usage + worktree cwd to inspect how Claude edits files in-place.

### 2025-11-09 Stage 1
- `ob1 run` now wires Claude directly: we build repo context → prompt → Claude edits the isolated worktree → guardrail verifies paths → commit/push/PR.
- Successfully ran `k=3` against `Sanchay-T/ob1-sandbox`, producing PRs #6–#8 with polished login experiences.
- Tests (`pytest`) cover scope parsing + change guard utilities.
- Transcripts stored under `.ob1/transcripts/` per branch for auditing.

## Stage 2 Preview
- GitHub Action in `ob1-sandbox`:
  - Install deps, run tests/build.
  - Launch preview server + run Playwright to record short video.
  - Upload artifacts + comment with score & leaderboard update.

## Open Questions / To Discuss
1. Claude agent interaction style: single-shot diff vs. interactive repair loop?
2. How much repo context to feed initially (file map, key files, acceptance criteria)?
3. QA route to hit for the login page (confirm `/` vs. `/login`).
