# 🗺️ ob1 Implementation Roadmap

## Stage 1: MVP (Current - 2 hours) ✅

**Goal:** 3 PRs from parallel agents

**Status:** COMPLETE

### Completed Components

- ✅ Configuration Manager (`ob1/utils/config.py`)
  - Environment variable loading
  - API key validation
  - Secret masking

- ✅ Agent Protocol (`ob1/agents/base.py`)
  - Abstract `Agent` interface
  - Standardized `AgentResult`
  - Extensible for future agents

- ✅ Claude Agent (`ob1/agents/claude.py`)
  - Direct Anthropic API integration (Python 3.9 compatible)
  - Cost tracking
  - Timeout handling

- ✅ Worktree Manager (`ob1/workspace/worktree.py`)
  - Git worktree creation
  - Branch management
  - Cleanup utilities

- ✅ GitHub PR Creator (`ob1/workspace/github_pr.py`)
  - Commit changes
  - Push branches
  - Create PRs via PyGithub

- ✅ Orchestrator (`ob1/orchestrator.py`)
  - Parallel agent execution
  - Progress tracking (Rich UI)
  - Result aggregation

- ✅ CLI (`ob1/cli.py`)
  - Click-based interface
  - `-m/--message` and `-k/--agents` flags

### What Works

```bash
ob1 -m "Build a React login component" -k 3
```

**Output:**
- 3 git worktrees created
- 3 Claude agents run in parallel
- 3 PRs created on GitHub
- Rich progress bars
- Cost and timing summary

---

## Stage 2: Real Agent Integration (Next 4 hours)

**Goal:** Replace mock Claude implementation with actual working agents

### Priority 1: Claude Agent SDK (Python 3.10+)

**File:** `ob1/agents/claude.py`

**Implementation:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def execute(self, task: str, workspace_path: str, branch_name: str) -> AgentResult:
    options = ClaudeAgentOptions(
        cwd=workspace_path,
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Write", "Edit", "Bash"],
        max_budget_usd=self.max_budget_usd,
        api_key=self.api_key
    )

    changes = []
    cost = 0.0

    async for message in query(prompt=task, options=options):
        # Track file changes
        if message.type == "tool_call" and message.tool_name in ["Write", "Edit"]:
            changes.append(message.tool_input.get("file_path"))

        # Track cost
        if message.type == "result" and hasattr(message, "usage"):
            cost = calculate_cost(message.usage)

    return AgentResult(
        agent_id=f"claude-{branch_name}",
        status="success",
        branch_name=branch_name,
        changes_made=changes,
        cost_usd=cost
    )
```

**Requirements:**
- Upgrade to Python 3.10+ OR use Docker container
- Install: `pip install claude-agent-sdk`
- Test with real task

**ETA:** 2 hours

---

### Priority 2: Aider Integration

**File:** `ob1/agents/aider.py`

**Implementation:**
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

class AiderAgent:
    async def execute(self, task: str, workspace_path: str, branch_name: str) -> AgentResult:
        # Setup headless mode
        io = InputOutput(yes=True)
        model = Model(self.model)

        # Find files to edit (or create new ones)
        files = self._detect_files(workspace_path, task)

        # Run aider
        coder = Coder.create(
            main_model=model,
            fnames=files,
            io=io,
            auto_commits=False
        )

        coder.run(task)

        return AgentResult(
            agent_id=f"aider-{branch_name}",
            status="success",
            branch_name=branch_name,
            changes_made=files,
            cost_usd=self._calculate_cost(coder)
        )
```

**Requirements:**
- Install: `pip install aider-chat`
- Handle file discovery
- Extract cost from Aider output

**ETA:** 1.5 hours

---

### Priority 3: Goose Integration

**File:** `ob1/agents/goose.py`

**Implementation Strategy:** CLI Wrapper

```python
class GooseAgent:
    async def execute(self, task: str, workspace_path: str, branch_name: str) -> AgentResult:
        # Create recipe file
        recipe_path = f"{workspace_path}/.goose-recipe.yaml"
        self._create_recipe(recipe_path, task)

        # Run goose
        proc = await asyncio.create_subprocess_exec(
            "goose", "run", "--recipe", recipe_path,
            cwd=workspace_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        # Parse output
        changes = self._extract_changes(stdout.decode())

        return AgentResult(
            agent_id=f"goose-{branch_name}",
            status="success" if proc.returncode == 0 else "failed",
            branch_name=branch_name,
            changes_made=changes
        )
```

**Requirements:**
- Install Goose CLI
- Create recipe format
- Parse output

**ETA:** 0.5 hours

---

## Stage 3: AgentAPI Integration (4-6 hours)

**Goal:** Support 10+ agents via unified HTTP interface

### Architecture

```
ob1/agents/
├── base.py              # Agent protocol
├── claude.py            # Direct Claude SDK
├── aider.py             # Direct Aider API
├── goose.py             # Direct Goose CLI
└── agentapi_adapter.py  # NEW: Universal adapter
```

### Implementation: AgentAPI Adapter

**File:** `ob1/agents/agentapi_adapter.py`

```python
import httpx
import asyncio
import subprocess

class AgentAPIAdapter:
    """Run ANY agent via AgentAPI HTTP interface"""

    SUPPORTED_AGENTS = [
        "claude",      # Claude Code via AgentAPI
        "aider",       # Aider via AgentAPI
        "goose",       # Goose via AgentAPI
        "cursor",      # Cursor CLI
        "copilot",     # GitHub Copilot CLI
        "cody",        # Sourcegraph Cody
        "gemini",      # Google Gemini
    ]

    def __init__(self, agent_type: str, port: int = None):
        if agent_type not in self.SUPPORTED_AGENTS:
            raise ValueError(f"Unsupported agent: {agent_type}")

        self.agent_type = agent_type
        self.port = port or self._get_free_port()
        self.base_url = f"http://localhost:{self.port}"
        self.process = None

    async def start_server(self, workspace: str, **kwargs):
        """Start AgentAPI server for this agent"""
        cmd = [
            "agentapi", "server",
            "--port", str(self.port),
            "--",
            self.agent_type,
            "--cwd", workspace
        ]

        # Add agent-specific args
        if "api_key" in kwargs:
            cmd.extend(["--api-key", f"{self.agent_type}={kwargs['api_key']}"])
        if "model" in kwargs:
            cmd.extend(["--model", kwargs["model"]])

        self.process = subprocess.Popen(cmd)

        # Wait for server startup
        await self._wait_for_ready()

    async def _wait_for_ready(self):
        """Poll until server responds"""
        for _ in range(30):  # 30 second timeout
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/status")
                    if response.status_code == 200:
                        return
            except:
                pass
            await asyncio.sleep(1)

        raise Exception(f"AgentAPI server failed to start on port {self.port}")

    async def send_message(self, content: str):
        """Send task to agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/message",
                json={"content": content, "type": "user"}
            )
            return response.json()

    async def wait_for_completion(self, timeout: int = 600):
        """Wait until agent finishes"""
        start = time.time()

        while time.time() - start < timeout:
            status = await self.get_status()
            if status == "stable":
                return True
            await asyncio.sleep(2)

        return False  # Timeout

    async def get_status(self) -> str:
        """Get agent status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/status")
            return response.json().get("status")

    async def get_messages(self) -> list:
        """Get all messages"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/messages")
            return response.json()

    async def shutdown(self):
        """Stop AgentAPI server"""
        if self.process:
            self.process.terminate()
            self.process.wait()

    def _get_free_port(self) -> int:
        """Find available port"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]


class AgentAPIAgent:
    """Agent implementation using AgentAPI"""

    def __init__(self, agent_type: str, **config):
        self.agent_type = agent_type
        self.config = config
        self.adapter = None

    async def execute(
        self,
        task: str,
        workspace_path: str,
        branch_name: str
    ) -> AgentResult:
        start_time = time.time()

        try:
            # Start AgentAPI server
            self.adapter = AgentAPIAdapter(self.agent_type)
            await self.adapter.start_server(workspace_path, **self.config)

            # Send task
            await self.adapter.send_message(task)

            # Wait for completion
            success = await self.adapter.wait_for_completion()

            # Get results
            messages = await self.adapter.get_messages()

            # Parse changes from messages
            changes = self._extract_changes(messages)

            duration = time.time() - start_time

            return AgentResult(
                agent_id=f"{self.agent_type}-{branch_name}",
                status="success" if success else "timeout",
                branch_name=branch_name,
                changes_made=changes,
                duration_seconds=duration
            )

        finally:
            # Cleanup
            if self.adapter:
                await self.adapter.shutdown()

    def _extract_changes(self, messages: list) -> list:
        """Extract file changes from AgentAPI messages"""
        changes = []
        for msg in messages:
            # Parse message content for file operations
            # This depends on agent-specific output format
            if "type" in msg and msg["type"] in ["tool_use", "file_edit"]:
                if "file_path" in msg:
                    changes.append(msg["file_path"])
        return changes
```

### CLI Enhancement

**File:** `ob1/cli.py`

Add `--agent-type` flag:

```python
@click.option(
    '--agent-type',
    multiple=True,
    default=['claude'],
    help='Agent types to use (can specify multiple: --agent-type claude --agent-type aider)'
)
def main(message: str, agents: int, agent_type: tuple, ...):
    # If multiple agent types specified, distribute across k agents
    agent_pool = list(agent_type) * (agents // len(agent_type) + 1)
    agent_pool = agent_pool[:agents]

    # Pass to orchestrator
    results = orchestrator.run(message, agent_pool)
```

**Usage:**
```bash
# 3 Claude agents
ob1 -m "Build login" -k 3

# Mix of agents
ob1 -m "Build login" -k 5 --agent-type claude --agent-type aider --agent-type goose

# All via AgentAPI
ob1 -m "Build login" -k 3 --use-agentapi --agent-type cursor
```

---

## Stage 4: Quality & Polish (2-3 hours)

### Features to Add

1. **Result Comparison**
   - Side-by-side PR diff view
   - Quality scoring (lines changed, test coverage, etc.)
   - Winner selection

2. **Cost Budgeting**
   - `--max-cost` flag
   - Stop agents when budget exceeded
   - Cost predictions

3. **Agent Health Checks**
   - Verify agents installed
   - Check API keys valid
   - Friendly error messages

4. **Retry Logic**
   - Auto-retry failed agents (up to 3 times)
   - Exponential backoff

5. **Logging & Observability**
   - Structured logs (JSON)
   - Agent execution traces
   - Export to file

### Testing

- Unit tests for each agent
- Integration tests for orchestrator
- End-to-end test with real repo

---

## Stage 5: Documentation & Demo (1-2 hours)

### Documentation to Create

1. **README.md** - Installation, quickstart, examples
2. **CONTRIBUTING.md** - How to add new agents
3. **API.md** - Python API documentation
4. **AGENTS.md** - Supported agents, configuration

### Demo Preparation

**Script:**
```bash
# 1. Show help
ob1 --help

# 2. Run simple task with 3 agents
ob1 -m "Add a header component to the React app" -k 3

# 3. Show results
# - 3 PRs created
# - Cost breakdown
# - Time comparison

# 4. Show flexibility - different agents
ob1 -m "Refactor error handling" -k 3 \
    --agent-type claude \
    --agent-type aider \
    --agent-type goose

# 5. Show AgentAPI power
ob1 -m "Add dark mode toggle" -k 5 --use-agentapi \
    --agent-type cursor \
    --agent-type copilot \
    --agent-type cody \
    --agent-type claude \
    --agent-type aider
```

**Metrics to Highlight:**
- ✅ 5 agents running in parallel
- ✅ 5 PRs created in < 2 minutes
- ✅ Total cost: $1.20
- ✅ 10+ agents supported
- ✅ Extensible architecture

---

## Dependencies Installation

### Current Setup (Python 3.9)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Installed:**
- click
- httpx
- gitpython
- pygithub
- anthropic
- rich
- pydantic

### Stage 2 Requirements (Python 3.10+)

**Option A: Upgrade Python**
```bash
# macOS
brew install python@3.10

# Create new venv
python3.10 -m venv .venv310
source .venv310/bin/activate
pip install -e .
pip install claude-agent-sdk aider-chat
```

**Option B: Docker**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -e .
RUN pip install claude-agent-sdk aider-chat

CMD ["ob1", "--help"]
```

### Stage 3 Requirements (AgentAPI)

```bash
# Install AgentAPI
go install github.com/coder/agentapi/cmd/agentapi@latest

# Or via Homebrew (if available)
brew install agentapi

# Verify
agentapi --version
```

---

## Success Metrics

### MVP (Stage 1) ✅
- [x] 3 PRs created from parallel agents
- [x] Rich terminal UI
- [x] Cost tracking
- [x] Extensible agent interface

### Production Ready (Stage 2-4)
- [ ] 3+ real agents integrated (Claude, Aider, Goose)
- [ ] AgentAPI adapter working
- [ ] 80%+ test coverage
- [ ] Complete documentation
- [ ] Error handling for all edge cases

### Impressive Demo (Stage 5)
- [ ] 5+ agents running simultaneously
- [ ] < 2 minute end-to-end time
- [ ] Beautiful terminal output
- [ ] Live cost/performance metrics
- [ ] Easy agent swapping demo

---

## Timeline Summary

| Stage | Task | Time | Status |
|-------|------|------|--------|
| 1 | MVP Implementation | 2h | ✅ COMPLETE |
| 2 | Real Agent Integration | 4h | 🔄 NEXT |
| 3 | AgentAPI Integration | 4-6h | ⏳ PENDING |
| 4 | Quality & Polish | 2-3h | ⏳ PENDING |
| 5 | Documentation & Demo | 1-2h | ⏳ PENDING |
| **Total** | | **13-17h** | |

**MVP to Production:** ~13-17 hours of focused development

---

## Risk Mitigation

### Risk: Python 3.10+ Requirement

**Solutions:**
1. Use Docker container
2. Install Python 3.10 via Homebrew/apt
3. Fall back to Anthropic API directly (current approach)

### Risk: Agent Installation Complexity

**Solutions:**
1. Provide Docker image with all agents pre-installed
2. Create installation script (`install_agents.sh`)
3. Document manual installation clearly

### Risk: API Rate Limits

**Solutions:**
1. Implement exponential backoff
2. Add `--max-parallel` limit
3. Respect rate limit headers

### Risk: Cost Overruns

**Solutions:**
1. `--max-cost` budget enforcement
2. Cost estimation before execution
3. Require confirmation for expensive tasks

---

**Ready to impress stakeholders!** 🚀
