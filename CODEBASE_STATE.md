# 🏗️ CODEBASE STATE - Complete Architecture

**Purpose:** Understand how everything works, where everything is
**Audience:** New agent needing deep architectural knowledge
**Read Time:** 15 minutes

---

## 📂 REPOSITORY STRUCTURE

### open-code-blocks (Main CLI Tool)

```
/Users/sanchay/Documents/open-code-blocks/
├── src/ob1/                      # Main source code (2,500+ lines)
│   ├── cli.py                    # CLI entry point (Typer)
│   ├── orchestrator.py           # Core orchestration logic
│   ├── providers/                # AI provider implementations
│   │   ├── base.py               # Provider protocol
│   │   ├── claude.py             # Claude Agent SDK integration
│   │   ├── cursor.py             # Cursor CLI wrapper (HAS BUG)
│   │   └── codex.py              # OpenAI GPT-4o integration
│   ├── ui/                       # NEW: Beautiful dashboard UI
│   │   ├── __init__.py
│   │   ├── theme.py              # Colors, emojis, constants
│   │   ├── agent_panel.py        # Per-agent panel rendering
│   │   ├── dashboard.py          # Live dashboard orchestrator
│   │   └── animations.py         # Splash, celebrations
│   ├── utils/                    # Utilities
│   │   └── timer.py              # Time tracking
│   ├── repo_manager.py           # Git worktree management
│   ├── github_api.py             # GitHub REST API client
│   ├── qa_agent.py               # Stage 2: QA review logic
│   ├── context_engine.py         # Repo context gathering
│   ├── change_guard.py           # Scope validation
│   ├── diff_utils.py             # Diff parsing/application
│   ├── git_ops.py                # Git command wrappers
│   ├── path_filters.py           # Glob pattern matching
│   ├── settings.py               # Environment variable loading
│   └── claude_probe.py           # Claude one-off queries
├── tests/                        # Unit tests
│   ├── test_change_guard.py
│   ├── test_context_engine.py
│   └── test_path_filters.py
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
│   ├── validate_keys.py          # API key validation
│   ├── smoke_claude.py           # Claude smoke test
│   └── smoke_codex.py            # Codex smoke test
├── .venv/                        # Python virtual environment
├── pyproject.toml                # Project metadata
├── requirements.txt              # Python dependencies
├── .env                          # API keys (gitignored)
├── MASTER_HANDOFF.md             # This handoff! (NEW)
├── ISSUES_AND_FIXES.md           # Bug fixes (NEW)
├── CODEBASE_STATE.md             # This file (NEW)
└── ...                           # Other handoff docs

Lines of Code:
- Core CLI: ~1,700 lines
- UI Module: ~800 lines (NEW)
- Providers: ~400 lines
- Total: ~2,900 lines Python
```

### ob1-sandbox (Target Repository)

```
/Users/sanchay/Documents/ob1-sandbox/
├── frontend/                     # React + Vite application
│   ├── src/
│   │   ├── App.jsx               # Main app component
│   │   ├── main.jsx              # Entry point
│   │   ├── components/           # React components
│   │   │   ├── Login.jsx         # Login page (from earlier PRs)
│   │   │   ├── Navbar.jsx        # Navbar (from earlier PRs)
│   │   │   └── Dashboard/        # Dashboard (from PR #28)
│   │   ├── App.css
│   │   └── index.css
│   ├── tests/qa/
│   │   └── login.spec.ts         # Playwright test
│   ├── playwright.config.ts      # Playwright configuration
│   ├── package.json
│   ├── vite.config.js
│   └── ...
├── .github/workflows/
│   └── qa.yml                    # QA workflow (HAS BUG)
└── README.md

Purpose: Demo repo where ob1 creates PRs for testing
GitHub: https://github.com/Sanchay-T/ob1-sandbox
```

---

## 🔌 KEY MODULES DEEP DIVE

### 1. CLI Entry Point (`cli.py`)

**Purpose:** Command-line interface using Typer

**Commands:**
```python
@app.command("run")           # Main: Run k agents in parallel
@app.command("qa")            # QA: Review a PR with Claude
@app.command("doctor")        # Diagnostics: Check repo/git status
@app.command("mkworktree")    # Utils: Create git worktree manually
@app.command("claude-ping")   # Debug: One-off Claude query
```

**Key Function:**
```python
def run(
    message: str,              # Task description
    k: int = 1,               # Number of parallel agents
    providers: str = "claude,cursor,codex",
    base: str = "main",
    scope: str | None = None,  # Glob patterns for allowed files
    target: str | None = None, # Target repo URL
    env_file: Path | None = None,
    dry_run: bool = False,
):
    config = RunConfig(...)
    asyncio.run(run_orchestrator(config, console))
```

**Flow:**
1. Parse CLI arguments
2. Create RunConfig
3. Call orchestrator
4. Display results

---

### 2. Orchestrator (`orchestrator.py`)

**Purpose:** Core orchestration logic for parallel agents

**Key Function:**
```python
async def run_orchestrator(config: RunConfig, console: Console):
    # 1. Show splash screen
    show_splash(console)

    # 2. Setup repo
    repo_manager = TargetRepoManager(...)
    repo_ctx = await repo_manager.prepare()

    # 3. Create live dashboard
    dashboard = LiveDashboard(...)

    # 4. Build providers
    provider_instances = _build_providers(...)

    # 5. Create k agent tasks
    tasks = []
    for idx in range(config.k):
        task = asyncio.create_task(_run_single_agent(...))
        tasks.append((agent_name, task))

    # 6. Run with live updates
    with Live(dashboard.render(), refresh_per_second=4):
        while pending_tasks:
            done, pending = await asyncio.wait(...)
            for task in done:
                res = await task
                dashboard.update_agent(...)
                live.update(dashboard.render())

    # 7. Show celebration or errors
    if all_success:
        celebrate_success(...)
    else:
        show_error_summary(...)

    # 8. Render final summary table
    _render_summary(results, console)
```

**Per-Agent Workflow (`_run_single_agent`):**
```python
async def _run_single_agent(...):
    # 1. Create git worktree
    worktree = repo_manager.create_worktree(branch)

    # 2. Gather repo context (files matching scope)
    context = gather_repo_context(worktree, scope_patterns)

    # 3. Build prompt with context
    prompt = build_prompt_text(message, scope_patterns, context)

    # 4. Run provider
    result = await provider.run(
        agent_name=agent_name,
        branch=branch,
        prompt=prompt,
        worktree=worktree,
        ...
    )

    # 5. Apply diff (if provider returned one)
    if result.diff_text:
        apply_unified_diff(result.diff_text, worktree)

    # 6. Validate scope (ensure changes within allowed patterns)
    files = list_changed_files(worktree)
    ensure_changes_within_scope(files, scope_patterns)

    # 7. Commit changes
    run_git("add", "-A", cwd=worktree)
    run_git("commit", "-m", f"feat: {agent_name} - {message}", cwd=worktree)

    # 8. Push branch
    run_git("push", "origin", branch, cwd=worktree)

    # 9. Create PR via GitHub API
    pr_url = await gh_client.create_pull_request(...)

    # 10. Cleanup worktree
    repo_manager.remove_worktree(branch, worktree)

    return AgentResult(
        agent_name=agent_name,
        branch=branch,
        status="success",
        pr_url=pr_url,
    )
```

---

### 3. Providers (`providers/`)

**Architecture:** Protocol-based for easy extensibility

**Base Protocol (`base.py`):**
```python
@dataclass
class ProviderResult:
    transcript_path: Path | None  # Path to full transcript/log
    diff_text: str | None = None  # Unified diff text (optional)

class AgentProvider(Protocol):
    name: str

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
        ...
```

**Claude Provider (`claude.py`):**
```python
class ClaudeProvider(AgentProvider):
    name = "claude"

    def __init__(self, api_key: str, console: Console):
        self._api_key = api_key
        self._console = console
        self._activity_tracker = {}  # For smart logging

    async def run(...) -> ProviderResult:
        # 1. Set up Claude Agent SDK options
        options = ClaudeAgentOptions(
            cwd=str(worktree),
            system_prompt=self._system_prompt,
            allowed_tools=None,  # All tools enabled
            permission_mode="acceptEdits",
        )

        # 2. Stream events from Claude SDK
        events = []
        async for message in query(prompt=prompt, options=options):
            events.append(message)
            self._log_event(agent_name, message)  # Smart logging

        # 3. Persist full transcript
        transcript_path = self._persist_transcript(repo_root, branch, events)

        # 4. Return (Claude applies changes directly, no diff needed)
        return ProviderResult(transcript_path=transcript_path)

    def _log_event(self, agent_name: str, message: object):
        # SMART FILTERING (NEW!)
        # - Filters out SystemMessage/UserMessage spam
        # - Groups tool calls (shows "🔍 Discovery (5 actions)" instead of spam)
        # - Tracks phases (Discovery → Implementation → Verification)
        # - Only logs significant events
        ...
```

**Cursor Provider (`cursor.py`):**
```python
class CursorProvider(AgentProvider):
    name = "cursor"

    async def run(...) -> ProviderResult:
        # 1. Run cursor-agent CLI
        proc = await asyncio.create_subprocess_exec(
            "cursor-agent",
            "-p", prompt,
            "--output-format", "text",
            cwd=worktree,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        # 2. Save transcript
        transcript_path = save_transcript(repo_root, branch, "cursor", stdout)

        # 3. Check if cursor modified files directly
        status = run_git("status", "--porcelain", cwd=worktree)
        if status.strip():
            # Cursor modified files, use git diff
            diff_output = run_git("diff", cwd=worktree)
            return ProviderResult(
                transcript_path=transcript_path,
                diff_text=diff_output,
                apply_diff=False,  # ❌ BUG HERE! Remove this line
            )

        # 4. Extract diff from cursor output
        diff_text = extract_diff_block(stdout)
        sanitized_diff, dropped = _sanitize_cursor_diff(diff_text, worktree)

        return ProviderResult(
            transcript_path=transcript_path,
            diff_text=sanitized_diff
        )
```

**Codex Provider (`codex.py`):**
```python
class CodexProvider(AgentProvider):
    name = "codex"

    def __init__(self, api_key: str, console: Console):
        self._client = AsyncOpenAI(api_key=api_key)
        self._max_attempts = 2  # Retry logic!

    async def run(...) -> ProviderResult:
        system_prompt = self._build_system_prompt(scope_patterns)
        messages = [{"role": "user", "content": prompt}]

        # Retry loop (up to 2 attempts)
        for attempt in range(1, self._max_attempts + 1):
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
            )

            # Extract diff
            diff_text = extract_diff_block(response.choices[0].message.content)

            # Validate scope
            patch = unidiff.PatchSet(diff_text)  # ❌ CAN CRASH HERE
            scope_issue = self._validate_scope(patch, scope_patterns)

            if not scope_issue:
                # Success!
                return ProviderResult(
                    transcript_path=transcript_path,
                    diff_text=diff_text
                )

            # Retry with failure reason
            retry_prompt = self._build_retry_instruction(scope_patterns, failure_reason)
            messages.append({"role": "user", "content": retry_prompt})

        raise RuntimeError("Codex failed after retries")
```

---

### 4. UI Module (`ui/`) - NEW!

**Purpose:** Beautiful live dashboard for real-time agent visualization

**Theme (`theme.py`):**
```python
# Provider visual identity
PROVIDER_COLORS = {
    "claude": "magenta",  # 🟣
    "cursor": "blue",     # 🔵
    "codex": "green",     # 🟢
}

PROVIDER_EMOJIS = { "claude": "🟣", "cursor": "🔵", "codex": "🟢" }

STATUS_EMOJIS = {
    "pending": "⏸️",
    "running": "⏳",
    "success": "✓",
    "failed": "✗",
    "dry-run": "🔍"
}

PHASE_EMOJIS = {
    "discovery": "🔍",
    "implementation": "✏️",
    "verification": "🧪",
    "finalization": "🚀"
}

PROGRESS_FULL = "█"
PROGRESS_EMPTY = "░"
```

**Agent Panel (`agent_panel.py`):**
```python
class AgentPanel:
    """Renders a beautiful panel for a single agent."""

    def __init__(self, agent_name: str, provider: str):
        self.agent_name = agent_name
        self.provider = provider
        self.color = PROVIDER_COLORS.get(provider, "white")
        self.status = "pending"
        self.metrics = {'elapsed': 0, 'files': 0, 'tools': 0}
        self.current_activity = "Initializing..."
        self.phases = {}
        self.pr_url = None

    def render(self) -> Panel:
        # Build content
        content = []
        content.append("⏱ 00:32 │ 📝 7 files │ 🛠️ 12 tools │ +156")
        content.append("")
        content.append("🔍 Discovery    ████████████ ✓ (5s)")
        content.append("✏️  Implementation ████████████ ✓ (15s)")
        content.append("")
        content.append("PR created successfully!")
        content.append("🔗 PR #28")

        return Panel(
            "\n".join(content),
            title=f"🟣 {self.agent_name}",
            subtitle="✓ SUCCESS",
            border_style=self.color,
        )
```

**Live Dashboard (`dashboard.py`):**
```python
class LiveDashboard:
    """Real-time dashboard for k parallel agents."""

    def __init__(self, agent_names, providers, task, console):
        self.agent_panels = {
            name: AgentPanel(name, provider)
            for name, provider in zip(agent_names, providers)
        }

    def render(self) -> Group:
        components = []
        components.append(self.create_header(...))
        for panel in self.agent_panels.values():
            components.append(panel.render())
        components.append(self.create_footer(...))
        return Group(*components)

    def update_agent(self, agent_name: str, **updates):
        panel = self.agent_panels[agent_name]
        if 'status' in updates:
            panel.update_status(updates['status'])
        # ... update other fields
```

**Animations (`animations.py`):**
```python
def show_splash(console: Console):
    """Show gradient OB1 logo on startup."""
    logo_gradient = Gradient(OB1_LOGO, colors=["cyan", "blue", "magenta"])
    console.print(Panel(logo_gradient, border_style="bold cyan"))

def celebrate_success(console, pr_count, total_time):
    """Show celebration when all agents succeed."""
    message = f"""
    ✨ SUCCESS! ✨
    {pr_count} Pull Requests Created
    Completed in {total_time}
    """
    console.print(Panel(message, border_style="bold green"))
```

---

### 5. Repository Manager (`repo_manager.py`)

**Purpose:** Git worktree lifecycle management

**Key Class:**
```python
class TargetRepoManager:
    def prepare(self) -> RepoContext:
        """Clone target repo or use current directory."""
        if self.target_url:
            # Clone to temp directory
            run_root = Path(tempfile.mkdtemp(prefix="ob1-run-"))
            target_path = run_root / "target"
            run_git("clone", "--origin", "origin", self.target_url, str(target_path))
            self._root = target_path
            self._is_cloned = True
        else:
            # Use current directory
            self._root = Path.cwd()
            self._is_cloned = False

        return RepoContext(root=self._root, ...)

    def create_worktree(self, branch: str) -> Path:
        """Create isolated git worktree for an agent."""
        work_dir = self._root / ".ob1" / "worktrees" / branch.replace("/", "-")
        work_dir.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:  # Thread-safe!
            run_git("worktree", "add", "-b", branch, str(work_dir), self.base_branch)

        return work_dir

    def remove_worktree(self, branch: str, path: Path):
        """Cleanup worktree after agent completes."""
        with self._lock:
            run_git("worktree", "remove", "--force", str(path))
            run_git("branch", "-D", branch)  # Delete local branch
```

**Why Worktrees:**
- Each agent gets isolated filesystem
- No conflicts between parallel agents
- Clean rollback on failure
- Shared .git directory (efficient)

---

### 6. QA Agent (`qa_agent.py`)

**Purpose:** Claude-powered PR review for CI/CD

**Key Function:**
```python
async def run_qa_review(config: QAReviewConfig, console: Console):
    # 1. Fetch PR metadata from GitHub API
    gh = GitHubAPI(settings.github_token)
    pr = await gh.get_pull_request(config.repo_ref, config.pr_number)
    files = await gh.list_pr_files(config.repo_ref, config.pr_number)

    # 2. Load build/test logs
    build_log = config.build_log_path.read_text()[-6000:]  # Tail
    test_log = config.test_log_path.read_text()[-6000:]

    # 3. Build QA prompt
    prompt = _render_prompt(pr, files, build_log, test_log, artifacts)

    # 4. Run Claude review
    response = await claude_ping(prompt, system_prompt="You are OB1 QA...")

    # 5. Post comment to PR
    if not config.dry_run:
        await gh.create_pr_comment(
            config.repo_ref,
            config.pr_number,
            response
        )
```

---

## 🔄 DATA FLOW DIAGRAMS

### Stage 1: Parallel Agents

```
User Command
    ↓
CLI (cli.py)
    ↓
RunConfig
    ↓
Orchestrator (orchestrator.py)
    ├→ show_splash()
    ├→ TargetRepoManager.prepare()
    ├→ _build_providers()
    └→ LiveDashboard
        ↓
For each of k agents (parallel):
    ↓
_run_single_agent()
    ├→ create_worktree()
    ├→ gather_repo_context()
    ├→ build_prompt_text()
    ├→ provider.run()
    │   └→ Claude SDK / Cursor CLI / OpenAI API
    ├→ apply_unified_diff()
    ├→ ensure_changes_within_scope()
    ├→ git commit
    ├→ git push
    ├→ create_pull_request()
    └→ remove_worktree()
        ↓
AgentResult
    ↓
Update LiveDashboard
    ↓
Show celebration/errors
    ↓
Render summary table
```

### Stage 2: QA Review

```
PR Created (GitHub)
    ↓
GitHub Actions Trigger (qa.yml)
    ├→ Checkout code
    ├→ Install deps
    ├→ npm run build → build.log
    ├→ npm run preview
    ├→ playwright test → playwright.log
    ├→ Upload artifacts (videos)
    └→ Install Claude CLI ❌ PATH ISSUE
        ↓
ob1 qa --pr N (qa_agent.py)
    ├→ Fetch PR metadata (GitHub API)
    ├→ Fetch changed files
    ├→ Read build.log
    ├→ Read playwright.log
    ├→ Build QA prompt
    ├→ Run Claude review (claude_ping)
    └→ Post comment to PR
```

---

## 🗄️ KEY DATA STRUCTURES

### RunConfig
```python
@dataclass
class RunConfig:
    message: str                  # Task description
    k: int                       # Number of agents
    providers: List[str]         # ["claude", "cursor", "codex"]
    base_branch: str             # "main"
    scope_patterns: List[str]    # ["frontend/**"]
    target_url: Optional[str]    # GitHub URL
    dry_run: bool                # Skip PR creation
    env_file: Optional[Path]
```

### AgentResult
```python
@dataclass
class AgentResult:
    agent_name: str              # "claude-1"
    branch: str                  # "ob1/20251109-080031/claude-1"
    status: str                  # "success" | "failed" | "dry-run"
    pr_url: Optional[str]        # "https://github.com/.../pull/28"
    error: Optional[str]         # Error message if failed
    transcript_path: Optional[Path]  # Path to full transcript
```

### ProviderResult
```python
@dataclass
class ProviderResult:
    transcript_path: Path | None  # Path to JSON/log
    diff_text: str | None         # Unified diff (optional)
    # NOTE: No apply_diff field! (Cursor bug tries to pass this)
```

---

## 🔐 ENVIRONMENT VARIABLES

**Location:** `.env` file in project root

**Required:**
```bash
# For Claude provider
CLAUDE_API_KEY=sk-ant-api03-...

# For Codex provider
OPENAI_API_KEY=sk-proj-...
# OR
CODEX_CLI_KEY=sk-proj-...  # Fallback

# For Cursor provider (optional if CLI logged in)
CURSOR_API_KEY=key_...

# For GitHub PR creation
GITHUB_TOKEN=ghp_...
# OR use: gh auth login
```

**Discovery:** `settings.py` searches up directory tree for `.env`

---

## 🧪 TESTING INFRASTRUCTURE

### Unit Tests
```
tests/
├── test_change_guard.py      # Scope validation
├── test_context_engine.py    # Repo context gathering
└── test_path_filters.py      # Glob pattern matching
```

### Running Tests
```bash
pytest
pytest -v
pytest tests/test_change_guard.py
```

### Coverage
- Core logic: Well tested
- Providers: Not tested (integration-level)
- UI: Not tested (visual)
- QA agent: Not tested end-to-end

---

## 📦 DEPENDENCIES

### Core Dependencies (pyproject.toml)
```toml
[project.dependencies]
typer = ">=0.20.0"              # CLI framework
rich = ">=13.7.1"               # Terminal UI
httpx = ">=0.26.0"              # HTTP client (async)
pydantic = ">=2.5.0"            # Data validation
pydantic-settings = ">=2.1.0"   # Settings management
python-dotenv = ">=1.0.0"       # .env file loading
claude-agent-sdk = ">=0.1.4"    # Claude integration
openai = ">=1.0.0"              # Codex integration
unidiff = ">=0.7.5"             # Diff parsing

# NEW: UI enhancements
alive-progress = "^3.1.5"       # Progress bars
rich-gradient = "^1.0.0"        # Gradients
terminaltexteffects = "^0.10.0" # Animations
```

### Development Dependencies
```bash
pytest
mypy
ruff  # Linter
```

---

## 🚀 EXECUTION FLOW EXAMPLE

**Command:**
```bash
ob1 run -m "Build dashboard" -k 3 --target https://github.com/user/repo.git --scope "frontend/**"
```

**What Happens:**
1. **CLI** parses args → creates RunConfig
2. **Orchestrator** starts:
   - Shows splash screen
   - Clones target repo to `/tmp/ob1-run-xyz/target/`
   - Loads API keys from `.env`
   - Creates 3 provider instances (Claude, Cursor, Codex)
   - Creates LiveDashboard with 3 panels
3. **For each agent (parallel):**
   - Creates worktree: `.ob1/worktrees/ob1-20251109-080031-claude-1/`
   - Gathers context: Reads files matching `frontend/**`
   - Builds prompt: Includes task + context + scope constraints
   - Runs provider:
     - **Claude:** Streams events, tracks phases, makes changes
     - **Cursor:** Runs CLI, extracts diff ❌ CRASHES (bug)
     - **Codex:** Calls OpenAI API, generates diff ⚠️ May fail (parsing)
   - Applies diff (if any)
   - Validates scope (all changes in `frontend/**`)
   - Commits: `git commit -m "feat: claude-1 - Build dashboard"`
   - Pushes: `git push origin ob1/20251109-080031/claude-1`
   - Creates PR via GitHub API
   - Removes worktree
   - Updates dashboard with result
4. **After all complete:**
   - Shows celebration (if all succeeded) or error summary
   - Renders final summary table
   - Cleans up cloned repo (unless `OB1_PRESERVE_TMP=1`)

**Time:** ~5 minutes for complex tasks, ~30 seconds for simple tasks

---

**END OF CODEBASE STATE**

*Next: Read UI_TRANSFORMATION.md for UI implementation details*
