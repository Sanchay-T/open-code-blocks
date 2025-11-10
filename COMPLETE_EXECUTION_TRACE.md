# OB1 Complete Execution Trace

## Command
```bash
ob1 run -m "Build a login page" -k 3 --issue 42 --target https://github.com/user/repo.git --scope "frontend/**"
```

## Table of Contents
1. [Overview](#overview)
2. [Complete Call Stack](#complete-call-stack)
3. [Detailed Execution Flow](#detailed-execution-flow)
4. [State Changes](#state-changes)
5. [File I/O Operations](#file-io-operations)
6. [Network Operations](#network-operations)
7. [ASCII Flow Diagrams](#ascii-flow-diagrams)

---

## Overview

This command creates 3 parallel agents that work on building a login page, with changes scoped to `frontend/**`. The execution spawns:
- **Agent 1**: claude-1 (Claude provider)
- **Agent 2**: cursor-1 (Cursor provider)  
- **Agent 3**: codex-1 (Codex/OpenAI provider)

Each agent creates a PR associated with GitHub issue #42.

---

## Complete Call Stack

```
1. CLI Entry Point
   └─> cli.py:run() [L67-106]
       ├─> parse_scope() [L87]
       ├─> RunConfig() [L89-100]
       └─> asyncio.run(run_orchestrator()) [L103]

2. Orchestrator Setup
   └─> orchestrator.py:run_orchestrator() [L57-208]
       ├─> get_settings() [L64]
       ├─> TargetRepoManager.prepare() [L70-72]
       │   └─> repo_manager.py:prepare() [L37-61]
       │       ├─> _clone_target() [L69-78]
       │       ├─> parse_github_repo() [L49]
       │       └─> run_git("fetch") [L53]
       ├─> StateManager.create_run() [L86-94]
       │   └─> state_manager.py:create_run() [L108-133]
       ├─> LiveDashboard() [L107]
       ├─> _build_providers() [L115]
       │   └─> orchestrator.py:_build_providers() [L391-407]
       │       ├─> ClaudeProvider() [L396]
       │       ├─> CursorProvider() [L398]
       │       └─> CodexProvider() [L404]
       └─> asyncio.create_task(_run_single_agent()) × 3 [L136-149]

3. Agent Execution (×3 in parallel)
   └─> orchestrator.py:_run_single_agent() [L211-321]
       ├─> repo_manager.create_worktree() [L225]
       │   └─> repo_manager.py:create_worktree() [L80-87]
       ├─> gather_repo_context() [L227-231]
       │   └─> context_engine.py:gather_repo_context() [L17-47]
       ├─> build_prompt_text() [L232]
       │   └─> context_engine.py:build_prompt_text() [L67-119]
       ├─> provider.run() [L238-245]
       │   ├─> claude.py:ClaudeProvider.run() [L47-67]
       │   │   └─> _run_query() [L59]
       │   │       └─> claude_agent_sdk.query() [L82]
       │   ├─> cursor.py:CursorProvider.run() [L34-97]
       │   │   └─> asyncio.create_subprocess_exec() [L49]
       │   └─> codex.py:CodexProvider.run() [L27-91]
       │       └─> AsyncOpenAI.chat.completions.create() [L48]
       ├─> apply_unified_diff() [L247]
       │   └─> diff_utils.py:apply_unified_diff() [L10-23]
       ├─> ensure_changes_within_scope() [L251]
       │   └─> change_guard.py:ensure_changes_within_scope() [L31-39]
       ├─> _commit_all() [L252]
       │   └─> orchestrator.py:_commit_all() [L324-331]
       ├─> repo_manager.push_branch() [L253]
       │   └─> repo_manager.py:push_branch() [L102-105]
       ├─> gh_client.create_pull_request() [L271-277]
       │   └─> github_api.py:create_pull_request() [L60-82]
       ├─> state_mgr.track_pr() [L284-290]
       │   └─> state_manager.py:track_pr() [L210-231]
       └─> repo_manager.remove_worktree() [L321]

4. Cleanup & Summary
   └─> orchestrator.py:run_orchestrator() [L189-208]
       ├─> gh_client.close() [L190]
       ├─> repo_manager.cleanup() [L193]
       ├─> celebrate_success() / show_error_summary() [L202-206]
       └─> _render_summary() [L208]
```

---

## Detailed Execution Flow

### PHASE 1: CLI Entry & Argument Parsing

#### File: `src/ob1/cli.py`

**Function**: `run()` (Lines 67-106)

```python
67→@app.command()
68→def run(
69→    message: str = typer.Option(..., "-m", help="Task for agents, e.g. 'Build a login page'"),
70→    k: int = typer.Option(1, "-k", help="Number of parallel agents"),
71→    providers: str = typer.Option(
72→        "claude,cursor,codex",
73→        help="Comma-separated provider list (default: claude,cursor,codex)",
74→    ),
75→    base: str = typer.Option("main", help="Base ref for branches"),
76→    scope: Optional[str] = typer.Option(None, help="Allowed path (glob) for changes"),
77→    target: Optional[str] = typer.Option(None, help="Target repo URL; defaults to current repo"),
78→    env_file: Optional[Path] = typer.Option(None, help="Path to env file with tokens"),
79→    dry_run: bool = typer.Option(False, help="Plan actions without applying"),
80→    issue: Optional[int] = typer.Option(None, "--issue", help="GitHub issue number to associate with PRs"),
81→    continue_pr: Optional[int] = typer.Option(None, "--continue-pr", help="PR number to continue working on"),
82→):
83→    """Run k agents in parallel (initial implementation)."""
84→    provider_list = [p.strip() for p in providers.split(",") if p.strip()]
85→    if not provider_list:
86→        raise typer.BadParameter("At least one provider must be specified", param_hint="providers")
87→
88→    scope_patterns = parse_scope(scope)
```

**Input**:
- `message`: "Build a login page"
- `k`: 3
- `providers`: "claude,cursor,codex"
- `base`: "main"
- `scope`: "frontend/**"
- `target`: "https://github.com/user/repo.git"
- `issue`: 42

**Processing** (Line 84):
```python
provider_list = ["claude", "cursor", "codex"]
```

**File**: `src/ob1/path_filters.py` (Line 87 call)

**Function**: `parse_scope()` (Lines 7-18)

```python
7→def parse_scope(scope: str | None) -> List[str]:
8→    """Turn a comma/space separated scope string into glob patterns.
9→
10→    Defaults to ["**"] (everything) when scope is None/empty.
11→    """
12→
13→    if not scope:
14→        return ["**"]
15→
16→    raw_parts = [part.strip() for part in scope.replace(";", ",").split(",")]
17→    patterns = [part or "**" for part in raw_parts if part]
18→    return patterns or ["**"]
```

**Output**: `["frontend/**"]`

**Config Creation** (Lines 89-100):

```python
89→    config = RunConfig(
90→        message=message,
91→        k=k,
92→        providers=provider_list,
93→        base_branch=base,
94→        scope_patterns=scope_patterns,
95→        target_url=target,
96→        dry_run=dry_run,
97→        env_file=env_file,
98→        issue_number=issue,
99→        continue_pr=continue_pr,
100→    )
```

**Result**:
```python
RunConfig(
    message="Build a login page",
    k=3,
    providers=["claude", "cursor", "codex"],
    base_branch="main",
    scope_patterns=["frontend/**"],
    target_url="https://github.com/user/repo.git",
    dry_run=False,
    env_file=None,
    issue_number=42,
    continue_pr=None
)
```

**Launch Orchestrator** (Line 103):
```python
103→    try:
104→        asyncio.run(run_orchestrator(config, console))
```

---

### PHASE 2: Orchestrator Initialization

#### File: `src/ob1/orchestrator.py`

**Function**: `run_orchestrator()` (Lines 57-208)

```python
57→async def run_orchestrator(config: RunConfig, console: Console) -> None:
58→    if config.k < 1:
59→        raise ValueError("k must be >= 1")
60→
61→    # Show splash screen
62→    show_splash(console)
63→
64→    settings = get_settings(config.env_file)
```

**Settings Loading** (`src/ob1/settings.py`, Lines 45-58):

```python
45→@lru_cache()
46→def get_settings(env_file: Optional[Path] = None) -> Settings:
47→    env_source = env_file or _discover_env_file()
48→    kwargs = {}
49→    if env_source:
50→        kwargs["_env_file"] = env_source
51→    settings = Settings(**kwargs)
52→    if not settings.github_token:
53→        token = _gh_cli_token()
54→        if token:
55→            settings.github_token = token
56→    if not settings.openai_api_key and settings.codex_cli_key:
57→        settings.openai_api_key = settings.codex_cli_key
58→    return settings
```

**Output**:
```python
Settings(
    github_token="ghp_xxxx...",
    claude_api_key="sk-ant-...",
    cursor_api_key="cursor_...",
    openai_api_key="sk-...",
    codex_cli_key=None
)
```

**Seed Environment Variables** (Line 65, function Lines 431-440):

```python
431→def _seed_process_env(settings) -> None:
432→    env_mapping = {
433→        "CLAUDE_API_KEY": getattr(settings, "claude_api_key", None),
434→        "ANTHROPIC_API_KEY": getattr(settings, "claude_api_key", None),
435→        "OPENAI_API_KEY": getattr(settings, "openai_api_key", None),
436→        "CURSOR_API_KEY": getattr(settings, "cursor_api_key", None),
437→    }
438→    for key, value in env_mapping.items():
439→        if value and not os.environ.get(key):
440→            os.environ[key] = value
```

**State**: Environment variables now set for all providers.

---

### PHASE 3: Repository Setup

**Initialize TargetRepoManager** (Line 70):

```python
70→    repo_manager = TargetRepoManager(base_branch=config.base_branch, target_url=config.target_url)
```

**File**: `src/ob1/repo_manager.py`

**Constructor** (Lines 29-35):

```python
29→    def __init__(self, base_branch: str, target_url: Optional[str] = None) -> None:
30→        self.base_branch = base_branch
31→        self.target_url = target_url
32→        self._root: Optional[Path] = None
33→        self._is_cloned = False
34→        self._lock = Lock()
35→        self._tmp_root: Optional[Path] = None
```

**Prepare Repository** (Lines 71-72 in orchestrator, function Lines 37-61 in repo_manager):

```python
37→    def prepare(self) -> RepoContext:
38→        if self.target_url:
39→            self._clone_target()
40→        else:
41→            cwd = Path.cwd()
42→            if not (cwd / ".git").exists():
43→                raise GitError("Current directory is not a git repository; pass --target")
44→            self._root = cwd
45→            self._is_cloned = False
46→
47→        assert self._root is not None
48→        origin = get_origin_url(self._root)
49→        owner, name = parse_github_repo(origin)
50→        repo_ref = RepoRef(owner=owner, name=name, origin_url=origin)
51→
52→        # Ensure base branch is up to date
53→        run_git("fetch", "origin", self.base_branch, cwd=self._root)
```

**Clone Target** (Lines 69-78):

```python
69→    def _clone_target(self) -> None:
70→        assert self.target_url
71→        run_root = Path(tempfile.mkdtemp(prefix="ob1-run-"))
72→        target_path = run_root / "target"
73→        target_path.parent.mkdir(parents=True, exist_ok=True)
74→        run_git("clone", "--origin", "origin", self.target_url, str(target_path))
75→        run_git("checkout", self.base_branch, cwd=target_path)
76→        self._root = target_path
77→        self._is_cloned = True
78→        self._tmp_root = run_root
```

**Git Commands Executed**:
1. `git clone --origin origin https://github.com/user/repo.git /tmp/ob1-run-xxxxx/target`
2. `git checkout main`
3. `git fetch origin main`

**Parse GitHub Repo** (`src/ob1/github_api.py`, Lines 13-29):

```python
13→def parse_github_repo(url: str) -> Tuple[str, str]:
14→    cleaned = url.strip()
15→    if cleaned.endswith(".git"):
16→        cleaned = cleaned[:-4]
17→
18→    if cleaned.startswith("git@github.com:"):
19→        path = cleaned.split(":", 1)[1]
20→    elif "github.com/" in cleaned:
21→        path = cleaned.split("github.com/", 1)[1]
22→    else:
23→        raise GitHubAPIError(f"Unsupported GitHub URL: {url}")
24→
25→    parts = [p for p in path.split("/") if p]
26→    if len(parts) < 2:
27→        raise GitHubAPIError(f"Cannot parse owner/repo from {url}")
28→    owner, repo = parts[0], parts[1]
29→    return owner, repo
```

**Output**: `("user", "repo")`

**RepoContext Created**:
```python
RepoContext(
    root=Path("/tmp/ob1-run-xxxxx/target"),
    base_branch="main",
    repo_ref=RepoRef(
        owner="user",
        name="repo",
        origin_url="https://github.com/user/repo.git"
    ),
    is_cloned=True
)
```

---

### PHASE 4: State Management Setup

**Create Run ID** (Line 78 in orchestrator):

```python
78→    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
```

**Example Output**: `"20251109-143025"`

**Initialize State Manager** (Line 83):

```python
83→    state_mgr = StateManager(repo_ctx.root)
```

**File**: `src/ob1/state_manager.py`

**Constructor** (Lines 69-80):

```python
69→    def __init__(self, repo_root: Path):
70→        self.repo_root = repo_root
71→        self.state_dir = repo_root / ".ob1" / "state"
72→        self.state_dir.mkdir(parents=True, exist_ok=True)
73→        self.runs_file = self.state_dir / "runs.json"
74→        self.pr_tracking_file = self.state_dir / "pr_tracking.json"
75→
76→        # Initialize state files if they don't exist
77→        if not self.runs_file.exists():
78→            self._write_runs([])
79→        if not self.pr_tracking_file.exists():
80→            self._write_pr_tracking([])
```

**File System State**:
```
/tmp/ob1-run-xxxxx/target/.ob1/state/
├── runs.json (created)
└── pr_tracking.json (created)
```

**Create Run State** (Lines 86-95 in orchestrator):

```python
86→    state_mgr.create_run(
87→        run_id=run_id,
88→        message=config.message,
89→        target_repo=f"{repo_ctx.repo_ref.owner}/{repo_ctx.repo_ref.name}",
90→        base_branch=config.base_branch,
91→        scope_patterns=config.scope_patterns,
92→        k=config.k,
93→        issue_number=config.issue_number,
94→    )
95→    state_mgr.update_run_status(run_id, "running")
```

**state_manager.py** `create_run()` (Lines 108-133):

```python
108→    def create_run(
109→        self,
110→        run_id: str,
111→        message: str,
112→        target_repo: str,
113→        base_branch: str,
114→        scope_patterns: List[str],
115→        k: int,
116→        issue_number: Optional[int] = None,
117→    ) -> RunState:
118→        """Create a new run state."""
119→        run = RunState(
120→            run_id=run_id,
121→            message=message,
122→            target_repo=target_repo,
123→            base_branch=base_branch,
124→            scope_patterns=scope_patterns,
125→            issue_number=issue_number,
126→            k=k,
127→            status="pending",
128→        )
129→
130→        runs = self._read_runs()
131→        runs.append(run)
132→        self._write_runs(runs)
133→        return run
```

**File Write**: `/tmp/ob1-run-xxxxx/target/.ob1/state/runs.json`
```json
{
  "runs": [
    {
      "run_id": "20251109-143025",
      "message": "Build a login page",
      "target_repo": "user/repo",
      "base_branch": "main",
      "scope_patterns": ["frontend/**"],
      "issue_number": 42,
      "k": 3,
      "created_at": "2025-11-09T14:30:25.123456",
      "status": "running",
      "agents": []
    }
  ]
}
```

---

### PHASE 5: Provider Setup

**Create Agent Names** (Lines 98-104):

```python
98→    agent_names = []
99→    provider_list = []
100→    for idx in range(config.k):
101→        provider = config.providers[idx % len(config.providers)]
102→        agent_name = f"{provider}-{idx + 1}"
103→        agent_names.append(agent_name)
104→        provider_list.append(provider)
```

**Result**:
- `agent_names = ["claude-1", "cursor-2", "codex-3"]`
- `provider_list = ["claude", "cursor", "codex"]`

**Initialize Providers** (Lines 114-115):

```python
114→        with console.status(f"[bold cyan]Preparing {len(set(config.providers))} provider(s)...", spinner="dots"):
115→            provider_instances = _build_providers(config.providers, settings, console)
```

**Function**: `_build_providers()` (Lines 391-407):

```python
391→def _build_providers(provider_names: List[str], settings, console: Console) -> dict[str, AgentProvider]:
392→    providers: dict[str, AgentProvider] = {}
393→    for name in set(provider_names):
394→        if name == "claude":
395→            # Remove noisy credential logging - credentials are validated elsewhere
396→            providers[name] = _build_claude_provider(settings, console)
397→        elif name == "cursor":
398→            providers[name] = CursorProvider(console=console)
399→        elif name == "codex":
400→            api_key = settings.openai_api_key
401→            # Remove noisy credential logging
402→            if not api_key:
403→                raise RuntimeError("OPENAI_API_KEY (or CODEX_CLI_KEY) is required for provider 'codex'")
404→            providers[name] = CodexProvider(api_key=api_key, console=console)
405→        else:
406→            raise RuntimeError(f"Unsupported provider '{name}'")
407→    return providers
```

**Claude Provider** (Lines 410-428):

```python
410→def _build_claude_provider(settings, console: Console) -> ClaudeProvider:
411→    api_key = settings.claude_api_key
412→    if not api_key:
413→        raise RuntimeError("CLAUDE_API_KEY is required for Claude-based providers")
414→    return ClaudeProvider(
415→        api_key=api_key,
416→        console=console,
417→        allowed_tools=[
418→            "Task",
419→            "Read",
420→            "Write",
421→            "Edit",
422→            "NotebookEdit",
423→            "Glob",
424→            "Grep",
425→            "Bash",
426→            "BashOutput",
427→        ],
428→    )
```

**Result**:
```python
provider_instances = {
    "claude": ClaudeProvider(api_key="sk-ant-...", console=..., allowed_tools=[...]),
    "cursor": CursorProvider(console=...),
    "codex": CodexProvider(api_key="sk-...", console=...)
}
```

---

### PHASE 6: Parallel Agent Execution

**Create Tasks** (Lines 123-150):

```python
123→        with Live(dashboard.render(), console=console, refresh_per_second=4, transient=False) as live:
124→            tasks: List[asyncio.Task[AgentResult]] = []
125→            for idx in range(config.k):
126→                provider = config.providers[idx % len(config.providers)]
127→                agent_name = f"{provider}-{idx + 1}"
128→                branch = f"ob1/{run_id}/{agent_name}"
129→
130→                # Add agent to state
131→                state_mgr.add_agent_to_run(run_id, agent_name, provider, branch)
132→
133→                # Mark as running in dashboard
134→                dashboard.update_agent(agent_name, status='running', activity='Starting...')
135→                live.update(dashboard.render())
136→
137→                task = asyncio.create_task(
138→                    _run_single_agent(
139→                        agent_name=agent_name,
140→                        branch=branch,
141→                        provider_name=provider,
142→                        provider=provider_instances[provider],
143→                        config=config,
144→                        repo_ctx=repo_ctx,
145→                        repo_manager=repo_manager,
146→                        gh_client=gh_client,
147→                        state_mgr=state_mgr,
148→                        run_id=run_id,
149→                    )
150→                )
151→                tasks.append((agent_name, task))
```

**Agent Branches Created**:
- Agent 1: `ob1/20251109-143025/claude-1`
- Agent 2: `ob1/20251109-143025/cursor-2`
- Agent 3: `ob1/20251109-143025/codex-3`

**State Updated** (`state_manager.py`, Lines 144-164):

```python
144→    def add_agent_to_run(
145→        self,
146→        run_id: str,
147→        agent_name: str,
148→        provider: str,
149→        branch: str,
150→    ) -> None:
151→        """Add an agent to a run."""
152→        runs = self._read_runs()
153→        for run in runs:
154→            if run.run_id == run_id:
155→                agent = AgentRunState(
156→                    name=agent_name,
157→                    provider=provider,
158→                    branch=branch,
159→                    status="pending",
160→                    started_at=datetime.utcnow().isoformat(),
161→                )
162→                run.agents.append(agent)
163→                break
164→        self._write_runs(runs)
```

---

### PHASE 7: Single Agent Execution (×3 in parallel)

**Function**: `_run_single_agent()` (Lines 211-321)

We'll trace **Agent 1 (claude-1)** in detail. Agents 2 and 3 follow the same flow.

```python
211→async def _run_single_agent(
212→    agent_name: str,
213→    branch: str,
214→    provider_name: str,
215→    provider: AgentProvider,
216→    config: RunConfig,
217→    repo_ctx: RepoContext,
218→    repo_manager: TargetRepoManager,
219→    gh_client: Optional[GitHubAPI],
220→    state_mgr: StateManager,
221→    run_id: str,
222→) -> AgentResult:
223→    worktree_path: Optional[Path] = None
224→    try:
225→        worktree_path = await asyncio.to_thread(repo_manager.create_worktree, branch)
```

#### Step 7.1: Create Worktree

**File**: `src/ob1/repo_manager.py`, Lines 80-87:

```python
80→    def create_worktree(self, branch: str) -> Path:
81→        if self._root is None:
82→            raise GitError("Repository not prepared")
83→        work_dir = self._root / ".ob1" / "worktrees" / branch.replace("/", "-")
84→        work_dir.parent.mkdir(parents=True, exist_ok=True)
85→        with self._lock:
86→            run_git("worktree", "add", "-b", branch, str(work_dir), self.base_branch, cwd=self._root)
87→        return work_dir
```

**Git Command**:
```bash
git worktree add -b ob1/20251109-143025/claude-1 \
  /tmp/ob1-run-xxxxx/target/.ob1/worktrees/ob1-20251109-143025-claude-1 \
  main
```

**Result**:
```python
worktree_path = Path("/tmp/ob1-run-xxxxx/target/.ob1/worktrees/ob1-20251109-143025-claude-1")
```

**File System**:
```
/tmp/ob1-run-xxxxx/target/.ob1/worktrees/
├── ob1-20251109-143025-claude-1/  (full repo copy on branch ob1/20251109-143025/claude-1)
├── ob1-20251109-143025-cursor-2/  (full repo copy on branch ob1/20251109-143025/cursor-2)
└── ob1-20251109-143025-codex-3/   (full repo copy on branch ob1/20251109-143025/codex-3)
```

---

#### Step 7.2: Gather Repository Context

**Code** (Lines 227-231):

```python
227→        prompt_context = await asyncio.to_thread(
228→            gather_repo_context,
229→            worktree_path,
230→            config.scope_patterns,
231→        )
```

**File**: `src/ob1/context_engine.py`, Lines 17-47:

```python
17→def gather_repo_context(
18→    worktree: Path,
19→    patterns: Iterable[str],
20→    max_files: int = 20,  # Increased from 8
21→    max_chars_per_file: int = 2000,  # Increased from 600
22→) -> RepoContext:
23→    matched_files: List[Path] = []
24→    ignore_roots = {".git", ".ob1", "node_modules"}
25→    for path in sorted(worktree.rglob("*")):
26→        if len(matched_files) >= max_files:
27→            break
28→        if not path.is_file():
29→            continue
30→        rel = path.relative_to(worktree).as_posix()
31→        if any(part in ignore_roots for part in rel.split("/")):
32→            continue
33→        if matches_any(rel, patterns):
34→            matched_files.append(path)
35→
36→    snippets: List[str] = []
37→    for path in matched_files:
38→        rel = path.relative_to(worktree).as_posix()
39→        try:
40→            text = path.read_text(encoding="utf-8")
41→        except UnicodeDecodeError:
42→            continue
43→        snippet = text[:max_chars_per_file]
44→        snippets.append(f"### {rel}\n````text\n{snippet}\n````")
45→
46→    package_summary = _summarize_package_json(worktree)
47→    return RepoContext(file_snippets=snippets, package_summary=package_summary)
```

**Files Read** (example):
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/components/Header.tsx`
- `frontend/vite.config.ts`
- ... (up to 20 files matching `frontend/**`)

**Output**:
```python
RepoContext(
    file_snippets=[
        "### frontend/package.json\n````text\n{...}\n````",
        "### frontend/src/App.tsx\n````text\n...\n````",
        ...
    ],
    package_summary="Package `frontend` scripts: {'dev': 'vite', 'build': 'vite build'}. Key deps: react, react-dom, ..."
)
```

---

#### Step 7.3: Build Prompt

**Code** (Line 232):

```python
232→        prompt_text = build_prompt_text(config.message, config.scope_patterns, prompt_context)
```

**File**: `src/ob1/context_engine.py`, Lines 67-119:

```python
67→def build_prompt_text(task: str, scope_patterns: Iterable[str], context: RepoContext) -> str:
68→    scope_text = ", ".join(scope_patterns)
69→    file_section = "\n\n".join(context.file_snippets)
70→    package_section = context.package_summary
71→    instructions = f"""
72→You are ob1, an elite frontend engineer tasked with implementing features with production-level quality.
73→
74→Task:
75→{task}
76→
77→Constraints:
78→- Only edit files matching: {scope_text}
79→- Changes must be buildable via `npm install && npm run build` inside `frontend/`.
80→- Keep code clean, properly typed (TypeScript/JSDoc), and ensure responsive design.
81→- If a new page/component is created, update routing configuration so it's accessible.
82→- IMPORTANT: Create Playwright test files for any new routes or significant features.
83→
84→Project Summary:
85→{package_section}
86→
87→Current Codebase Context:
88→{file_section}
89→
90→Critical Requirements:
91→1. **Code Quality**: Write clean, maintainable code following existing patterns in the codebase.
92→2. **Complete Implementation**: Implement the full feature including UI, logic, validation, and error handling.
93→3. **Routing Integration**: If adding new pages, ensure they're properly integrated into the routing system (React Router, etc.).
94→4. **Test Coverage**: For new routes/features, create Playwright tests in `frontend/tests/` directory:
95→   - Test file naming: `<feature-name>.spec.ts`
96→   - Test critical user flows (navigation, form submission, error states)
97→   - Include proper assertions for UI elements
98→5. **Consistency**: Maintain styling consistency with existing components.
99→6. **Build Validation**: Ensure `npm run build` succeeds after changes.
100→
101→Structure Guidelines:
102→- Components: Place in `frontend/src/components/` (organized by feature if appropriate)
103→- Pages: Place in `frontend/src/pages/` or appropriate routing directory
104→- Tests: Place in `frontend/tests/` with descriptive names
105→- Styles: Follow existing styling approach (CSS modules, Tailwind, etc.)
106→
107→Never:
108→- Remove or break existing unrelated functionality
109→- Create routes that don't exist (like /dashboard/root without implementing /dashboard first)
110→- Leave incomplete implementations
111→- Skip error handling or loading states
112→
113→When finished, the application should:
114→- Build successfully (`npm run build`)
115→- Have working routing to all new pages
116→- Include basic test coverage for new features
117→- Maintain visual consistency with existing UI
118→"""
119→    return instructions.strip()
```

**Output**: Multi-thousand character prompt with task, scope, codebase context, and requirements.

---

#### Step 7.4: Run Provider (Claude Example)

**Code** (Lines 238-245):

```python
238→            provider_result = await provider.run(
239→                agent_name=agent_name,
240→                branch=branch,
241→                prompt=prompt_text,
242→                worktree=worktree_path,
243→                repo_root=repo_ctx.root,
244→                scope_patterns=config.scope_patterns,
245→            )
```

**File**: `src/ob1/providers/claude.py`, Lines 47-67:

```python
47→    async def run(
48→        self,
49→        *,
50→        agent_name: str,
51→        branch: str,
52→        prompt: str,
53→        worktree: Path,
54→        repo_root: Path,
55→        scope_patterns: list[str],
56→    ) -> ProviderResult:
57→        transcript: List[object] = []
58→        try:
59→            transcript = await self._run_query(agent_name, prompt, worktree)
60→        except Exception as exc:  # noqa: BLE001
61→            events = transcript or getattr(exc, "_ob1_events", [])
62→            if events:
63→                self._persist_transcript(repo_root, branch, events)
64→            raise
65→
66→        transcript_path = self._persist_transcript(repo_root, branch, transcript)
67→        return ProviderResult(transcript_path=transcript_path)
```

**_run_query** (Lines 69-92):

```python
69→    async def _run_query(self, agent_name: str, prompt: str, worktree: Path) -> List[object]:
70→        os.environ["CLAUDE_API_KEY"] = self._api_key
71→        os.environ["ANTHROPIC_API_KEY"] = self._api_key
72→        options = ClaudeAgentOptions(
73→            allowed_tools=self._allowed_tools or None,
74→            permission_mode=self._permission_mode,
75→            cwd=str(worktree),
76→            system_prompt=self._system_prompt,
77→            setting_sources=["project", "user"],
78→        )
79→
80→        events: List[object] = []
81→        try:
82→            async for message in query(prompt=prompt, options=options):
83→                events.append(message)
84→                self._log_event(agent_name, message)
85→        except ClaudeSDKError as exc:
86→            self._console.print(f"[red]Claude SDK error ({agent_name}):[/red] {exc}")
87→            setattr(exc, "_ob1_events", events)
88→            raise
89→        except Exception as exc:  # noqa: BLE001
90→            setattr(exc, "_ob1_events", events)
91→            raise
92→        return events
```

**Claude SDK Call** (Line 82):
- Calls `claude_agent_sdk.query()` with the prompt
- Claude operates in the worktree directory
- Has access to tools: Task, Read, Write, Edit, Glob, Grep, Bash, etc.
- Claude reads files, analyzes code, creates new files
- All file operations happen in the worktree

**Example Tool Calls Made by Claude**:
1. `Glob(pattern="frontend/src/**/*.tsx")` - Find existing components
2. `Read(file_path="frontend/src/App.tsx")` - Read main app
3. `Read(file_path="frontend/src/main.tsx")` - Read entry point
4. `Write(file_path="frontend/src/pages/Login.tsx", content="...")` - Create login page
5. `Edit(file_path="frontend/src/App.tsx", ...)` - Add route
6. `Write(file_path="frontend/tests/login.spec.ts", content="...")` - Create test
7. `Bash(command="cd frontend && npm install && npm run build")` - Verify build

**Transcript Saved** (Lines 151-157):

```python
151→    def _persist_transcript(self, repo_root: Path, branch: str, events: Sequence[object]) -> Path:
152→        transcripts_dir = repo_root / ".ob1" / "transcripts"
153→        transcripts_dir.mkdir(parents=True, exist_ok=True)
154→        path = transcripts_dir / f"{branch.replace('/', '_')}.json"
155→        payload = [self._serialize_event(event) for event in events]
156→        path.write_text(json.dumps(payload, indent=2))
157→        return path
```

**File Written**: `/tmp/ob1-run-xxxxx/target/.ob1/transcripts/ob1_20251109-143025_claude-1.json`

**Return**:
```python
ProviderResult(
    transcript_path=Path("/tmp/ob1-run-xxxxx/target/.ob1/transcripts/ob1_20251109-143025_claude-1.json"),
    diff_text=None  # Claude directly modifies files
)
```

---

#### Step 7.5: Apply Changes (Cursor/Codex only)

**Code** (Lines 246-247):

```python
246→            if provider_result and provider_result.diff_text:
247→                await asyncio.to_thread(apply_unified_diff, provider_result.diff_text, worktree_path)
```

**File**: `src/ob1/diff_utils.py`, Lines 10-23:

```python
10→def apply_unified_diff(diff_text: str, worktree: Path) -> None:
11→    if not diff_text or not diff_text.strip():
12→        raise ValueError("No diff content returned by provider")
13→
14→    process = subprocess.run(  # noqa: S603
15→        ["git", "apply", "--whitespace=nowarn", "-"],
16→        input=diff_text.encode("utf-8"),
17→        cwd=worktree,
18→        capture_output=True,
19→        check=False,
20→    )
21→    if process.returncode != 0:
22→        stderr = process.stderr.decode().strip()
23→        raise RuntimeError(f"Failed to apply diff: {stderr}")
```

**Git Command** (for Cursor/Codex):
```bash
git apply --whitespace=nowarn - < diff_text
```

**Note**: Claude provider returns `diff_text=None` because it modifies files directly via tools.

---

#### Step 7.6: Validate Changes

**List Changed Files** (Line 248):

```python
248→            files = await asyncio.to_thread(list_changed_files, worktree_path)
```

**File**: `src/ob1/change_guard.py`, Lines 15-28:

```python
15→def list_changed_files(worktree: Path) -> List[str]:
16→    """Return paths (POSIX) with staged/unstaged changes."""
17→
18→    out = run_git("status", "--porcelain", cwd=worktree)
19→    files: List[str] = []
20→    for line in out.splitlines():
21→        if not line.strip():
22→            continue
23→        path_part = line[3:].lstrip()
24→        # Handle renames "R  a -> b"
25→        if " -> " in path_part:
26→            path_part = path_part.split(" -> ", 1)[1]
27→        files.append(path_part)
28→    return files
```

**Git Command**:
```bash
git status --porcelain
```

**Example Output**:
```
 M frontend/src/App.tsx
 M frontend/src/main.tsx
?? frontend/src/pages/Login.tsx
?? frontend/src/components/LoginForm.tsx
?? frontend/tests/login.spec.ts
```

**Parsed Files**:
```python
files = [
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/pages/Login.tsx",
    "frontend/src/components/LoginForm.tsx",
    "frontend/tests/login.spec.ts"
]
```

**Check No Files** (Lines 249-250):

```python
249→            if not files:
250→                raise ChangeGuardError("Agent did not modify any files")
```

**Validate Scope** (Line 251):

```python
251→            await asyncio.to_thread(ensure_changes_within_scope, files, config.scope_patterns)
```

**File**: `src/ob1/change_guard.py`, Lines 31-39:

```python
31→def ensure_changes_within_scope(files: Iterable[str], allowed_patterns: Iterable[str]) -> None:
32→    patterns = list(allowed_patterns)
33→    if not patterns:
34→        return
35→    bad = [path for path in files if not matches_any(path, patterns)]
36→    if bad:
37→        raise ChangeGuardError(
38→            "Changes outside allowed scope detected: " + ", ".join(bad)
39→        )
```

**Validation**:
- `allowed_patterns = ["frontend/**"]`
- All files start with `frontend/`
- **Validation passes** ✓

---

#### Step 7.7: Commit Changes

**Code** (Line 252):

```python
252→            await asyncio.to_thread(_commit_all, worktree_path, f"feat: {agent_name} - {config.message}")
```

**Function** (Lines 324-331):

```python
324→def _commit_all(worktree: Path, message: str) -> None:
325→    run_git("add", "-A", cwd=worktree)
326→    try:
327→        run_git("commit", "-m", message, cwd=worktree)
328→    except GitError as err:
329→        # No changes to commit
330→        if "nothing to commit" not in str(err):
331→            raise
```

**Git Commands**:
```bash
git add -A
git commit -m "feat: claude-1 - Build a login page"
```

**Commit Created**:
```
commit abc123def456...
Author: Your Name <your.email@example.com>
Date:   Sat Nov 9 14:30:45 2025 +0000

    feat: claude-1 - Build a login page
```

---

#### Step 7.8: Push Branch

**Code** (Line 253):

```python
253→            await asyncio.to_thread(repo_manager.push_branch, branch)
```

**File**: `src/ob1/repo_manager.py`, Lines 102-105:

```python
102→    def push_branch(self, branch: str) -> None:
103→        if self._root is None:
104→            raise GitError("Repository not prepared")
105→        run_git("push", "-u", "origin", f"{branch}:{branch}", cwd=self._root)
```

**Git Command**:
```bash
git push -u origin ob1/20251109-143025/claude-1:ob1/20251109-143025/claude-1
```

**Network**: Pushes to `https://github.com/user/repo.git`

---

#### Step 7.9: Create Pull Request

**Code** (Lines 255-277):

```python
255→            pr_title = f"{agent_name}: {config.message[:60]}"
256→
257→            # Build PR body with issue association
258→            issue_reference = f"\n\nCloses #{config.issue_number}" if config.issue_number else ""
259→            pr_body = textwrap.dedent(
260→                f"""
261→                Automated agent PR from `{provider_name}`.
262→
263→                - Agent: `{agent_name}`
264→                - Run ID: `{run_id}`
265→                - Task: {config.message}
266→                - Transcript saved locally at: {provider_result.transcript_path if provider_result else 'n/a'}
267→                {issue_reference}
268→                """
269→            ).strip()
270→
271→            pr_url = await gh_client.create_pull_request(
272→                repo=repo_ctx.repo_ref,
273→                title=pr_title,
274→                head=branch,
275→                base=repo_ctx.base_branch,
276→                body=pr_body,
277→            )
```

**PR Details**:
- **Title**: `claude-1: Build a login page`
- **Body**:
  ```
  Automated agent PR from `claude`.

  - Agent: `claude-1`
  - Run ID: `20251109-143025`
  - Task: Build a login page
  - Transcript saved locally at: /tmp/ob1-run-xxxxx/target/.ob1/transcripts/ob1_20251109-143025_claude-1.json

  Closes #42
  ```
- **Head**: `ob1/20251109-143025/claude-1`
- **Base**: `main`

**File**: `src/ob1/github_api.py`, Lines 60-82:

```python
60→    async def create_pull_request(
61→        self,
62→        repo: RepoRef,
63→        title: str,
64→        head: str,
65→        base: str,
66→        body: Optional[str] = None,
67→        draft: bool = False,
68→    ) -> str:
69→        payload = {
70→            "title": title,
71→            "head": head,
72→            "base": base,
73→            "draft": draft,
74→        }
75→        if body:
76→            payload["body"] = body
77→
78→        resp = await self._client.post(f"/repos/{repo.owner}/{repo.name}/pulls", json=payload)
79→        if resp.status_code not in {201, 202}:
80→            raise GitHubAPIError(f"Failed to create PR: {resp.status_code} {resp.text}")
81→        data = resp.json()
82→        return data.get("html_url") or ""
```

**HTTP Request**:
```
POST https://api.github.com/repos/user/repo/pulls
Headers:
  Accept: application/vnd.github+json
  Authorization: Bearer ghp_xxxx...
  User-Agent: ob1-cli
Body:
{
  "title": "claude-1: Build a login page",
  "head": "ob1/20251109-143025/claude-1",
  "base": "main",
  "body": "Automated agent PR from `claude`...\n\nCloses #42",
  "draft": false
}
```

**Response**:
```json
{
  "html_url": "https://github.com/user/repo/pull/123",
  "number": 123,
  ...
}
```

**Return**: `"https://github.com/user/repo/pull/123"`

---

#### Step 7.10: Track PR in State

**Code** (Lines 279-298):

```python
279→            # Extract PR number from URL (format: https://github.com/owner/repo/pull/123)
280→            pr_number = int(pr_url.split("/")[-1]) if pr_url else None
281→
282→            # Track PR in state
283→            if pr_number:
284→                state_mgr.track_pr(
285→                    pr_number=pr_number,
286→                    repo=f"{repo_ctx.repo_ref.owner}/{repo_ctx.repo_ref.name}",
287→                    branch=branch,
288→                    created_by_run=run_id,
289→                    issue_number=config.issue_number,
290→                )
291→                # Update agent state with PR info
292→                state_mgr.update_agent_status(
293→                    run_id=run_id,
294→                    agent_name=agent_name,
295→                    status="success",
296→                    pr_number=pr_number,
297→                    pr_url=pr_url,
298→                )
```

**File**: `src/ob1/state_manager.py`

**track_pr** (Lines 210-231):

```python
210→    def track_pr(
211→        self,
212→        pr_number: int,
213→        repo: str,
214→        branch: str,
215→        created_by_run: str,
216→        issue_number: Optional[int] = None,
217→    ) -> PRTrackingState:
218→        """Track a newly created PR."""
219→        pr_state = PRTrackingState(
220→            pr_number=pr_number,
221→            repo=repo,
222→            branch=branch,
223→            created_by_run=created_by_run,
224→            issue_number=issue_number,
225→            status="open",
226→        )
227→
228→        prs = self._read_pr_tracking()
229→        prs.append(pr_state)
230→        self._write_pr_tracking(prs)
231→        return pr_state
```

**File Write**: `/tmp/ob1-run-xxxxx/target/.ob1/state/pr_tracking.json`
```json
{
  "prs": [
    {
      "pr_number": 123,
      "repo": "user/repo",
      "branch": "ob1/20251109-143025/claude-1",
      "issue_number": 42,
      "created_by_run": "20251109-143025",
      "continuation_runs": [],
      "last_updated": "2025-11-09T14:30:50.123456",
      "status": "open"
    }
  ]
}
```

**update_agent_status** (Lines 166-195):

```python
166→    def update_agent_status(
167→        self,
168→        run_id: str,
169→        agent_name: str,
170→        status: str,
171→        pr_number: Optional[int] = None,
172→        pr_url: Optional[str] = None,
173→        error_message: Optional[str] = None,
174→        metrics: Optional[Dict[str, Any]] = None,
175→    ) -> None:
176→        """Update agent status and PR information."""
177→        runs = self._read_runs()
178→        for run in runs:
179→            if run.run_id == run_id:
180→                for agent in run.agents:
181→                    if agent.name == agent_name:
182→                        agent.status = status
183→                        if pr_number:
184→                            agent.pr_number = pr_number
185→                        if pr_url:
186→                            agent.pr_url = pr_url
187→                        if error_message:
188→                            agent.error_message = error_message
189→                        if metrics:
190→                            agent.metrics = metrics
191→                        if status in ("success", "failed"):
192→                            agent.completed_at = datetime.utcnow().isoformat()
193→                        break
194→                break
195→        self._write_runs(runs)
```

**File Update**: `/tmp/ob1-run-xxxxx/target/.ob1/state/runs.json`
```json
{
  "runs": [
    {
      "run_id": "20251109-143025",
      "message": "Build a login page",
      "target_repo": "user/repo",
      "base_branch": "main",
      "scope_patterns": ["frontend/**"],
      "issue_number": 42,
      "k": 3,
      "created_at": "2025-11-09T14:30:25.123456",
      "status": "running",
      "agents": [
        {
          "name": "claude-1",
          "provider": "claude",
          "branch": "ob1/20251109-143025/claude-1",
          "status": "success",
          "pr_number": 123,
          "pr_url": "https://github.com/user/repo/pull/123",
          "started_at": "2025-11-09T14:30:30.123456",
          "completed_at": "2025-11-09T14:30:50.123456",
          "error_message": null,
          "metrics": {}
        },
        ...
      ]
    }
  ]
}
```

---

#### Step 7.11: Return AgentResult

**Code** (Lines 302-308):

```python
302→        return AgentResult(
303→            agent_name=agent_name,
304→            branch=branch,
305→            status=status,
306→            pr_url=pr_url,
307→            transcript_path=provider_result.transcript_path if provider_result else None,
308→        )
```

**Result**:
```python
AgentResult(
    agent_name="claude-1",
    branch="ob1/20251109-143025/claude-1",
    status="success",
    pr_url="https://github.com/user/repo/pull/123",
    transcript_path=Path("/tmp/ob1-run-xxxxx/target/.ob1/transcripts/ob1_20251109-143025_claude-1.json")
)
```

---

#### Step 7.12: Cleanup Worktree

**Code** (Lines 319-321):

```python
319→    finally:
320→        if worktree_path is not None:
321→            await asyncio.to_thread(repo_manager.remove_worktree, branch, worktree_path)
```

**File**: `src/ob1/repo_manager.py`, Lines 89-100:

```python
89→    def remove_worktree(self, branch: str, path: Path) -> None:
90→        if self._root is None:
91→            return
92→        with self._lock:
93→            try:
94→                run_git("worktree", "remove", "--force", str(path), cwd=self._root)
95→            except GitError:
96→                pass
97→            try:
98→                run_git("branch", "-D", branch, cwd=self._root)
99→            except GitError:
100→                pass
```

**Git Commands**:
```bash
git worktree remove --force /tmp/ob1-run-xxxxx/target/.ob1/worktrees/ob1-20251109-143025-claude-1
git branch -D ob1/20251109-143025/claude-1
```

**Note**: Branch `ob1/20251109-143025/claude-1` is deleted locally but exists on remote.

---

### PHASE 8: Parallel Completion

**All 3 Agents Complete**:

The same flow (Steps 7.1-7.12) executes in parallel for all 3 agents:

**Agent 2 (cursor-2)**: Creates PR #124
**Agent 3 (codex-3)**: Creates PR #125

**State Files Updated**:

`/tmp/ob1-run-xxxxx/target/.ob1/state/pr_tracking.json`:
```json
{
  "prs": [
    {
      "pr_number": 123,
      "repo": "user/repo",
      "branch": "ob1/20251109-143025/claude-1",
      "issue_number": 42,
      "created_by_run": "20251109-143025",
      "continuation_runs": [],
      "last_updated": "2025-11-09T14:30:50.123456",
      "status": "open"
    },
    {
      "pr_number": 124,
      "repo": "user/repo",
      "branch": "ob1/20251109-143025/cursor-2",
      "issue_number": 42,
      "created_by_run": "20251109-143025",
      "continuation_runs": [],
      "last_updated": "2025-11-09T14:31:05.123456",
      "status": "open"
    },
    {
      "pr_number": 125,
      "repo": "user/repo",
      "branch": "ob1/20251109-143025/codex-3",
      "issue_number": 42,
      "created_by_run": "20251109-143025",
      "continuation_runs": [],
      "last_updated": "2025-11-09T14:31:10.123456",
      "status": "open"
    }
  ]
}
```

`/tmp/ob1-run-xxxxx/target/.ob1/state/runs.json`:
```json
{
  "runs": [
    {
      "run_id": "20251109-143025",
      "message": "Build a login page",
      "target_repo": "user/repo",
      "base_branch": "main",
      "scope_patterns": ["frontend/**"],
      "issue_number": 42,
      "k": 3,
      "created_at": "2025-11-09T14:30:25.123456",
      "status": "running",
      "agents": [
        {
          "name": "claude-1",
          "provider": "claude",
          "branch": "ob1/20251109-143025/claude-1",
          "status": "success",
          "pr_number": 123,
          "pr_url": "https://github.com/user/repo/pull/123",
          "started_at": "2025-11-09T14:30:30.123456",
          "completed_at": "2025-11-09T14:30:50.123456",
          "error_message": null,
          "metrics": {}
        },
        {
          "name": "cursor-2",
          "provider": "cursor",
          "branch": "ob1/20251109-143025/cursor-2",
          "status": "success",
          "pr_number": 124,
          "pr_url": "https://github.com/user/repo/pull/124",
          "started_at": "2025-11-09T14:30:30.123456",
          "completed_at": "2025-11-09T14:31:05.123456",
          "error_message": null,
          "metrics": {}
        },
        {
          "name": "codex-3",
          "provider": "codex",
          "branch": "ob1/20251109-143025/codex-3",
          "status": "success",
          "pr_number": 125,
          "pr_url": "https://github.com/user/repo/pull/125",
          "started_at": "2025-11-09T14:30:30.123456",
          "completed_at": "2025-11-09T14:31:10.123456",
          "error_message": null,
          "metrics": {}
        }
      ]
    }
  ]
}
```

---

### PHASE 9: Cleanup & Summary

**Back in orchestrator** (Lines 189-208):

**Close GitHub Client** (Lines 189-190):

```python
189→        if gh_client:
190→            await gh_client.close()
```

**Cleanup Repo** (Lines 192-193):

```python
192→    finally:
193→        repo_manager.cleanup()
```

**File**: `src/ob1/repo_manager.py`, Lines 63-67:

```python
63→    def cleanup(self) -> None:
64→        if os.environ.get("OB1_PRESERVE_TMP") == "1":
65→            return
66→        if self._is_cloned and self._tmp_root and self._tmp_root.exists():
67→            shutil.rmtree(self._tmp_root, ignore_errors=True)
```

**Action**: Deletes `/tmp/ob1-run-xxxxx/` (unless `OB1_PRESERVE_TMP=1`)

**Calculate Time** (Lines 196-199):

```python
196→    # Calculate total time
197→    total_time = time.time() - start_time
198→    mins = int(total_time // 60)
199→    secs = int(total_time % 60)
200→    time_str = f"{mins:02d}:{secs:02d}"
```

**Example**: `"00:45"` (45 seconds)

**Show Celebration** (Lines 202-206):

```python
202→    success_count = dashboard.get_success_count()
203→    if success_count == len(agent_names):
204→        celebrate_success(console, success_count, time_str)
205→    elif dashboard.get_failed_agents():
206→        show_error_summary(console, dashboard.get_failed_agents(), time_str)
```

**Render Summary** (Line 208):

```python
208→    _render_summary(agent_results, console)
```

**Function** (Lines 334-388):

```python
334→def _render_summary(results: List[AgentResult], console: Console) -> None:
335→    """Render beautiful summary table with emojis and colors."""
336→    from rich.panel import Panel
337→    from rich_gradient import Gradient
338→
339→    # Header with gradient
340→    header = Gradient(
341→        "🎉 Agent Run Complete!",
342→        colors=["cyan", "magenta", "yellow"]
343→    )
344→    console.print(Panel(header, border_style="bold cyan", padding=(0, 1)))
345→    console.print()  # Blank line
346→
347→    # Enhanced table
348→    table = Table(
349→        title="Agent Results",
350→        show_header=True,
351→        header_style="bold magenta",
352→        border_style="cyan",
353→        show_lines=False,
354→    )
355→    table.add_column("Agent", style="bold")
356→    table.add_column("Branch", style="dim")
357→    table.add_column("Status")
358→    table.add_column("PR")
359→    table.add_column("Error", style="red")
360→
361→    # Status emojis
362→    status_map = {
363→        "success": "[green]✓ success[/green]",
364→        "failed": "[red]✗ failed[/red]",
365→        "dry-run": "[yellow]🔍 dry-run[/yellow]",
366→    }
367→
368→    for res in results:
369→        # Add emoji to agent name based on provider
370→        agent_emoji = "🟣" if "claude" in res.agent_name else "🔵" if "cursor" in res.agent_name else "🟢"
371→        agent_display = f"{agent_emoji} {res.agent_name}"
372→
373→        # Format PR URL as clickable link (terminals with OSC 8 support)
374→        pr_display = "—"
375→        if res.pr_url:
376→            # Extract PR number from URL
377→            pr_num = res.pr_url.split("/")[-1]
378→            pr_display = f"[link={res.pr_url}]PR #{pr_num}[/link]"
379→
380→        table.add_row(
381→            agent_display,
382→            res.branch.split("/")[-1],  # Show only last part of branch
383→            status_map.get(res.status, res.status),
384→            pr_display,
385→            (res.error or "")[:80],
386→        )
387→
388→    console.print(table)
```

**Console Output**:
```
╭──────────────────────────────────────────────────────────╮
│             🎉 Agent Run Complete!                       │
╰──────────────────────────────────────────────────────────╯

                    Agent Results
┏━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Agent      ┃ Branch   ┃ Status    ┃ PR       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ 🟣 claude-1│ claude-1 │ ✓ success │ PR #123  │
│ 🔵 cursor-2│ cursor-2 │ ✓ success │ PR #124  │
│ 🟢 codex-3 │ codex-3  │ ✓ success │ PR #125  │
└────────────┴──────────┴───────────┴──────────┘
```

---

## State Changes

### State Progression Timeline

| Time | Event | State Change |
|------|-------|--------------|
| T+0s | CLI invoked | Parse arguments → RunConfig created |
| T+1s | Settings loaded | Environment variables seeded |
| T+2s | Repo cloned | `/tmp/ob1-run-xxxxx/target/` created |
| T+3s | Run state created | `.ob1/state/runs.json` created with run_id |
| T+4s | Providers initialized | ClaudeProvider, CursorProvider, CodexProvider ready |
| T+5s | Agent 1 started | Agent added to run state, worktree created |
| T+5s | Agent 2 started | Agent added to run state, worktree created |
| T+5s | Agent 3 started | Agent added to run state, worktree created |
| T+30s | Agent 1 completes | PR #123 created, state updated to "success" |
| T+35s | Agent 2 completes | PR #124 created, state updated to "success" |
| T+40s | Agent 3 completes | PR #125 created, state updated to "success" |
| T+41s | All complete | Worktrees removed, temp files cleaned |
| T+42s | Summary shown | Dashboard displayed, execution ends |

### File System State Changes

**Before Execution**:
```
/tmp/
└── (empty)
```

**During Execution**:
```
/tmp/ob1-run-xxxxx/
└── target/  (cloned repo)
    ├── .git/
    ├── frontend/
    ├── .ob1/
    │   ├── state/
    │   │   ├── runs.json
    │   │   └── pr_tracking.json
    │   ├── transcripts/
    │   │   ├── ob1_20251109-143025_claude-1.json
    │   │   ├── ob1_20251109-143025_cursor-2_cursor.log
    │   │   └── ob1_20251109-143025_codex-3_codex.log
    │   └── worktrees/
    │       ├── ob1-20251109-143025-claude-1/  (during agent execution)
    │       ├── ob1-20251109-143025-cursor-2/  (during agent execution)
    │       └── ob1-20251109-143025-codex-3/   (during agent execution)
    └── ...
```

**After Execution** (if `OB1_PRESERVE_TMP != 1`):
```
/tmp/
└── (empty - all cleaned up)
```

### Git State Changes

**Local Branches Created** (temporary, in worktrees):
- `ob1/20251109-143025/claude-1`
- `ob1/20251109-143025/cursor-2`
- `ob1/20251109-143025/codex-3`

**Remote Branches Created** (pushed to GitHub):
- `ob1/20251109-143025/claude-1` → Commit abc123
- `ob1/20251109-143025/cursor-2` → Commit def456
- `ob1/20251109-143025/codex-3` → Commit ghi789

**Local Branches Deleted** (after PR creation):
All 3 branches removed locally (but remain on remote)

---

## File I/O Operations

### Read Operations

1. **Settings Discovery**:
   - Read `.env` file (if exists)
   - Check environment variables

2. **Repository Context** (per agent, ~20 files each):
   - Read `frontend/package.json`
   - Read `frontend/src/**/*.tsx` (up to 20 files, 2000 chars each)
   - Read `frontend/src/**/*.ts`
   - Read `frontend/vite.config.ts`

3. **State Management**:
   - Read `.ob1/state/runs.json` (multiple times)
   - Read `.ob1/state/pr_tracking.json` (multiple times)

4. **Git Operations**:
   - Read git config for remote URLs
   - Read git status for changed files

### Write Operations

1. **Repository Setup**:
   - Clone entire repository to temp directory
   - Create `.ob1/state/` directory structure

2. **State Files**:
   - Write `.ob1/state/runs.json` (created, then updated 3+ times)
   - Write `.ob1/state/pr_tracking.json` (created, then updated 3 times)

3. **Agent Work** (per agent):
   - Create/modify files in `frontend/src/pages/`
   - Create/modify files in `frontend/src/components/`
   - Create test files in `frontend/tests/`
   - Modify routing files

4. **Transcripts** (per agent):
   - Write `.ob1/transcripts/ob1_20251109-143025_claude-1.json`
   - Write `.ob1/transcripts/ob1_20251109-143025_cursor-2_cursor.log`
   - Write `.ob1/transcripts/ob1_20251109-143025_codex-3_codex.log`

5. **Git Operations**:
   - Create worktree directories (3 full repo copies)
   - Commit changes (3 commits)

### Delete Operations

1. **Cleanup**:
   - Remove worktree directories (3 directories)
   - Delete local branches (3 branches)
   - Remove temp directory `/tmp/ob1-run-xxxxx/` (entire tree)

---

## Network Operations

### HTTP Requests

#### 1. GitHub API - Create Pull Request (×3)

**Request**:
```
POST https://api.github.com/repos/user/repo/pulls
Headers:
  Accept: application/vnd.github+json
  Authorization: Bearer ghp_xxxx...
  User-Agent: ob1-cli
Body:
{
  "title": "claude-1: Build a login page",
  "head": "ob1/20251109-143025/claude-1",
  "base": "main",
  "body": "Automated agent PR from `claude`.\n\n- Agent: `claude-1`\n- Run ID: `20251109-143025`\n- Task: Build a login page\n- Transcript saved locally at: /tmp/ob1-run-xxxxx/target/.ob1/transcripts/ob1_20251109-143025_claude-1.json\n\nCloses #42",
  "draft": false
}
```

**Response**:
```json
{
  "url": "https://api.github.com/repos/user/repo/pulls/123",
  "id": 123456789,
  "number": 123,
  "state": "open",
  "title": "claude-1: Build a login page",
  "body": "Automated agent PR from `claude`...",
  "html_url": "https://github.com/user/repo/pull/123",
  "head": {
    "ref": "ob1/20251109-143025/claude-1",
    ...
  },
  "base": {
    "ref": "main",
    ...
  },
  ...
}
```

**Same for PRs #124 and #125**

#### 2. Anthropic API - Claude Queries (Agent 1)

**Request**:
```
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: sk-ant-...
  anthropic-version: 2023-06-01
  content-type: application/json
Body:
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": "You are ob1, an elite frontend engineer...\n\nTask:\nBuild a login page\n\n..."
    }
  ],
  "system": "You are ob1, an elite frontend engineer...",
  "tools": [
    {"name": "Read", ...},
    {"name": "Write", ...},
    ...
  ]
}
```

**Response**: Streamed tool uses and text blocks

#### 3. OpenAI API - Codex Queries (Agent 3)

**Request**:
```
POST https://api.openai.com/v1/chat/completions
Headers:
  Authorization: Bearer sk-...
  Content-Type: application/json
Body:
{
  "model": "gpt-4o-mini",
  "temperature": 0.2,
  "max_tokens": 1800,
  "messages": [
    {
      "role": "system",
      "content": "You are Codex, an AI software engineer. Return ONLY a fenced ````diff```` block..."
    },
    {
      "role": "user",
      "content": "You are ob1, an elite frontend engineer...\n\nTask:\nBuild a login page\n\n..."
    }
  ]
}
```

**Response**:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "```diff\ndiff --git a/frontend/src/pages/Login.tsx b/frontend/src/pages/Login.tsx\n...\n```"
      }
    }
  ]
}
```

### Git Operations

#### 1. Clone Repository

```bash
git clone --origin origin https://github.com/user/repo.git /tmp/ob1-run-xxxxx/target
```

**Network**: Downloads entire repository

#### 2. Fetch Base Branch

```bash
git fetch origin main
```

**Network**: Downloads latest commits on main

#### 3. Push Branches (×3)

```bash
git push -u origin ob1/20251109-143025/claude-1:ob1/20251109-143025/claude-1
git push -u origin ob1/20251109-143025/cursor-2:ob1/20251109-143025/cursor-2
git push -u origin ob1/20251109-143025/codex-3:ob1/20251109-143025/codex-3
```

**Network**: Uploads commits and creates remote branches

---

## ASCII Flow Diagrams

### Overall System Flow

```
┌────────────────────────────────────────────────────────────────┐
│                        CLI Entry                                │
│  ob1 run -m "Build a login page" -k 3 --issue 42               │
│  --target https://github.com/user/repo.git --scope "frontend/**"│
└─────────────────────────┬──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Parse Arguments                               │
│  • message: "Build a login page"                                 │
│  • k: 3                                                          │
│  • providers: ["claude", "cursor", "codex"]                      │
│  • scope_patterns: ["frontend/**"]                               │
│  • issue_number: 42                                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Initialize Orchestrator                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Load Settings│  │  Clone Repo  │  │ Create State │           │
│  │ .env + gh    │  │  /tmp/...    │  │  runs.json   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Build Providers                                 │
│  ┌────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │   Claude   │    │   Cursor    │    │    Codex    │           │
│  │ SDK w/tools│    │  CLI spawn  │    │  OpenAI API │           │
│  └────────────┘    └─────────────┘    └─────────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Launch 3 Parallel Agent Tasks                       │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │   Agent 1     │  │   Agent 2     │  │   Agent 3     │        │
│  │  claude-1     │  │  cursor-2     │  │  codex-3      │        │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘        │
│          │                   │                   │                │
│          │                   │                   │                │
│     [Parallel Execution - See Agent Flow Below]                  │
│          │                   │                   │                │
│          ▼                   ▼                   ▼                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  PR #123      │  │  PR #124      │  │  PR #125      │        │
│  │  Closes #42   │  │  Closes #42   │  │  Closes #42   │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Cleanup & Summary                               │
│  • Close GitHub client                                           │
│  • Remove worktrees                                              │
│  • Delete temp directory                                         │
│  • Display success table                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Single Agent Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│              _run_single_agent(claude-1)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Create Worktree                                         │
│  git worktree add -b ob1/20251109-143025/claude-1 ...            │
│  → /tmp/ob1-run-xxxxx/target/.ob1/worktrees/ob1-...-claude-1     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Gather Repository Context                               │
│  • Scan worktree for files matching "frontend/**"                │
│  • Read up to 20 files (2000 chars each)                         │
│  • Parse package.json summary                                    │
│  → RepoContext with file snippets                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Build Prompt                                            │
│  • Combine task description                                      │
│  • Add scope constraints                                         │
│  • Inject codebase context                                       │
│  • Add requirements (tests, routing, build)                      │
│  → 5000+ character prompt                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Run Provider (Claude)                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  claude_agent_sdk.query()                                   │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Loop: Receive messages from Claude                   │  │ │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │  │ │
│  │  │  │ ToolUseBlock │  │ ToolUseBlock │  │  TextBlock  │ │  │ │
│  │  │  │ Read(...)    │  │ Write(...)   │  │  "Created..."│ │  │ │
│  │  │  └──────────────┘  └──────────────┘  └─────────────┘ │  │ │
│  │  │  • Glob("frontend/src/**/*.tsx")                      │  │ │
│  │  │  • Read("frontend/src/App.tsx")                       │  │ │
│  │  │  • Write("frontend/src/pages/Login.tsx", ...)         │  │ │
│  │  │  • Edit("frontend/src/App.tsx", add route)            │  │ │
│  │  │  • Write("frontend/tests/login.spec.ts", ...)         │  │ │
│  │  │  • Bash("cd frontend && npm run build")               │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │  → Events logged to transcript                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│  → ProviderResult(transcript_path, diff_text=None)              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Validate Changes                                        │
│  • git status --porcelain                                        │
│  • Parse changed files                                           │
│  • Ensure all files match "frontend/**"                          │
│  • Verify at least 1 file changed                                │
│  ✓ All checks pass                                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Commit & Push                                           │
│  • git add -A                                                    │
│  • git commit -m "feat: claude-1 - Build a login page"          │
│  • git push -u origin ob1/20251109-143025/claude-1              │
│  → Commit abc123 pushed to remote                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 7: Create Pull Request                                     │
│  POST /repos/user/repo/pulls                                     │
│  {                                                               │
│    title: "claude-1: Build a login page",                       │
│    head: "ob1/20251109-143025/claude-1",                         │
│    base: "main",                                                 │
│    body: "...\n\nCloses #42"                                     │
│  }                                                               │
│  → PR #123 created                                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 8: Update State                                            │
│  • Track PR in pr_tracking.json                                  │
│    - pr_number: 123                                              │
│    - issue_number: 42                                            │
│    - created_by_run: "20251109-143025"                           │
│  • Update agent status in runs.json                              │
│    - status: "success"                                           │
│    - pr_url: "https://github.com/user/repo/pull/123"            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 9: Cleanup                                                 │
│  • git worktree remove --force ...                               │
│  • git branch -D ob1/20251109-143025/claude-1                    │
│  → Worktree deleted, local branch removed                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Return: AgentResult                                             │
│  {                                                               │
│    agent_name: "claude-1",                                       │
│    branch: "ob1/20251109-143025/claude-1",                       │
│    status: "success",                                            │
│    pr_url: "https://github.com/user/repo/pull/123"              │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

### State Management Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     State Lifecycle                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Initialize: StateManager(repo_root)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Create .ob1/state/                                       │   │
│  │  ├── runs.json (empty)                                    │   │
│  │  └── pr_tracking.json (empty)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  create_run("20251109-143025", ...)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  runs.json += {                                           │   │
│  │    run_id: "20251109-143025",                             │   │
│  │    message: "Build a login page",                         │   │
│  │    target_repo: "user/repo",                              │   │
│  │    issue_number: 42,                                      │   │
│  │    k: 3,                                                  │   │
│  │    status: "pending",                                     │   │
│  │    agents: []                                             │   │
│  │  }                                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  update_run_status("20251109-143025", "running")                 │
│  → status: "running"                                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  add_agent_to_run(..., "claude-1", "claude", ...)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  agents += {                                              │   │
│  │    name: "claude-1",                                      │   │
│  │    provider: "claude",                                    │   │
│  │    branch: "ob1/20251109-143025/claude-1",                │   │
│  │    status: "pending",                                     │   │
│  │    started_at: "2025-11-09T14:30:30.123456"               │   │
│  │  }                                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ... repeat for cursor-2, codex-3                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agent Execution...                                              │
│  [See Agent Flow]                                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  track_pr(123, "user/repo", ..., issue_number=42)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  pr_tracking.json += {                                    │   │
│  │    pr_number: 123,                                        │   │
│  │    repo: "user/repo",                                     │   │
│  │    branch: "ob1/20251109-143025/claude-1",                │   │
│  │    issue_number: 42,                                      │   │
│  │    created_by_run: "20251109-143025",                     │   │
│  │    status: "open"                                         │   │
│  │  }                                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ... repeat for PRs #124, #125                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  update_agent_status(..., "claude-1", "success", pr_number=123)  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  agents[0] updated:                                       │   │
│  │    status: "success",                                     │   │
│  │    pr_number: 123,                                        │   │
│  │    pr_url: "https://github.com/user/repo/pull/123",      │   │
│  │    completed_at: "2025-11-09T14:30:50.123456"             │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ... repeat for cursor-2, codex-3                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Final State: All 3 agents succeeded                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  runs.json:                                               │   │
│  │    run_id: "20251109-143025"                              │   │
│  │    status: "running"  (could update to "completed")       │   │
│  │    agents: [                                              │   │
│  │      {claude-1: success, pr: #123},                       │   │
│  │      {cursor-2: success, pr: #124},                       │   │
│  │      {codex-3: success, pr: #125}                         │   │
│  │    ]                                                      │   │
│  │                                                           │   │
│  │  pr_tracking.json:                                        │   │
│  │    [{pr: #123, issue: 42}, {pr: #124, issue: 42},        │   │
│  │     {pr: #125, issue: 42}]                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This execution creates **3 parallel agents** that each:
1. Clone the target repository
2. Create isolated worktrees
3. Gather codebase context
4. Execute AI provider (Claude, Cursor, or Codex)
5. Make code changes scoped to `frontend/**`
6. Validate changes
7. Commit and push to new branches
8. Create pull requests linked to issue #42
9. Track state in JSON files
10. Clean up temporary resources

**Final Result**:
- 3 PRs created: #123, #124, #125
- All PRs reference issue #42 via "Closes #42"
- All changes scoped to `frontend/**`
- Complete execution tracked in `.ob1/state/`
- Transcripts saved for debugging
- Temporary files cleaned up

