# 🔬 Comprehensive AI Coding Agent Research Report

**For:** ob1 Parallel AI SWE Orchestrator
**Date:** January 2025
**Purpose:** Deep intelligence on orchestratable AI coding agents for impressive demo

---

## 📋 Executive Summary

We researched **10+ AI coding agents** to determine which can be orchestrated in parallel for the ob1 project. Key findings:

### ✅ Immediately Orchestratable (High Priority)

1. **Claude Agent SDK** - Official Anthropic agent, Python SDK, best for complex coding tasks
2. **Aider** - Python API + CLI, excellent for focused file edits
3. **Goose** - Open-source, local execution, multi-LLM support
4. **GitHub Copilot CLI** - Programmatic mode available, requires subscription

### 🔧 Orchestratable via AgentAPI (Unified Interface)

**AgentAPI** ([github.com/coder/agentapi](https://github.com/coder/agentapi)) provides a **unified HTTP API** to control:
- Claude Code
- Goose
- Aider
- GitHub Copilot CLI
- Gemini
- Cursor CLI (experimental)
- Amp, Codex, AmazonQ, and more

### 🎯 Recommended Architecture

```
ob1 Orchestrator
├── Direct Integration (Primary)
│   ├── Claude Agent SDK (Python)
│   ├── Aider (Python API)
│   └── Goose (CLI)
└── AgentAPI Integration (Future)
    ├── Cursor CLI
    ├── GitHub Copilot CLI
    └── Other emerging agents
```

---

## 🤖 Agent-by-Agent Deep Dive

### 1. Claude Agent SDK ⭐ PRIMARY

**Official Docs:** https://docs.claude.com/en/docs/agent-sdk/overview
**GitHub:** https://github.com/anthropics/claude-agent-sdk-python
**Maintainer:** Anthropic

#### Overview
Official Anthropic agent with autonomous coding capabilities. Renamed from "Claude Code SDK" to reflect broader vision beyond coding.

#### Installation
```bash
pip install claude-agent-sdk
# Requires Python 3.10+, Node.js, Claude Code 2.0.0+
npm install -g @anthropic-ai/claude-code
```

#### Programmatic Usage (Python)

**Simple Query:**
```python
from claude_agent_sdk import query

async for message in query(prompt="Build a login page"):
    print(message)
```

**Advanced Configuration:**
```python
from claude_agent_sdk import ClaudeAgentOptions, query

options = ClaudeAgentOptions(
    system_prompt="You are an expert React developer",
    max_turns=50,
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    permission_mode="acceptEdits",  # Auto-accept file changes
    cwd="/path/to/workspace",
    api_key="sk-ant-..."
)

async for message in query(prompt="Build login", options=options):
    # Process messages
    pass
```

#### Available Tools
- **File Operations:** Read, Write, Edit, Glob
- **Code Execution:** Bash
- **Search:** Grep
- **Web:** WebFetch, WebSearch
- **MCP Servers:** Custom tool integration via Model Context Protocol

#### Key Features for ob1

✅ **Headless Operation:** Fully automatable via Python API
✅ **Cost Tracking:** Built-in usage monitoring
✅ **Parallel Execution:** Async/await architecture supports concurrent agents
✅ **Error Handling:** Specific exceptions (CLINotFoundError, ProcessError, etc.)
✅ **Context Management:** Automatic compaction prevents context overflow
✅ **Tool Permissions:** Fine-grained control via allowedTools/disallowedTools

#### Authentication
- API Key: `ANTHROPIC_API_KEY` environment variable
- AWS Bedrock: `CLAUDE_CODE_USE_BEDROCK=1`
- Google Vertex AI: `CLAUDE_CODE_USE_VERTEX=1`

#### Cost Model
- Sonnet 4.5: $3/MTok input, $15/MTok output
- Trackable via usage API

#### Limitations
- Requires Python 3.10+ (blocker for some systems)
- Requires Node.js installation
- API may change (still evolving)

#### Integration Example for ob1
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_claude_agent(task: str, workspace: str, branch: str):
    options = ClaudeAgentOptions(
        cwd=workspace,
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Write", "Edit"],
        max_budget_usd=5.0
    )

    results = []
    async for msg in query(prompt=task, options=options):
        results.append(msg)

    return results
```

---

### 2. Aider ⭐ HIGH PRIORITY

**Website:** https://aider.chat
**GitHub:** https://github.com/Aider-AI/aider
**Maintainer:** Paul Gauthier (open-source)

#### Overview
AI pair programming tool optimized for editing existing code. Extremely popular (20k+ stars), active development, mature codebase.

#### Installation
```bash
pip install aider-chat
```

#### Programmatic Usage

**Command Line (Headless):**
```bash
aider --message "add error handling" --yes file.py
```

**Python API:**
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

# Headless mode
io = InputOutput(yes=True)
model = Model("gpt-4-turbo")
coder = Coder.create(main_model=model, fnames=["app.py"], io=io)

# Execute tasks
coder.run("add error handling to login function")
coder.run("write unit tests")
```

#### Key Features

✅ **Multi-Model Support:** GPT-4, Claude, Gemini, local models
✅ **Headless Mode:** `--yes` flag auto-approves changes
✅ **Git Integration:** Auto-commits with descriptive messages
✅ **Cost Tracking:** Built-in token usage display
✅ **Edit Quality:** Optimized for surgical code edits (better than raw LLM)

#### Available Flags for Automation
- `--message/-m`: Single instruction execution
- `--yes`: Auto-approve all changes
- `--no-auto-commits`: Disable automatic commits
- `--dry-run`: Preview changes without applying
- `--stream/--no-stream`: Toggle response streaming

#### Limitations

⚠️ **Python API Not Official:** "Could change without backwards compatibility"
⚠️ **Best for Edits:** Not ideal for greenfield projects (better: GPT-Engineer)

#### Integration Example for ob1
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

async def run_aider_agent(task: str, workspace: str, files: list):
    io = InputOutput(yes=True)
    model = Model("claude-sonnet-4-5")

    coder = Coder.create(
        main_model=model,
        fnames=files,
        io=io,
        auto_commits=False  # ob1 handles commits
    )

    coder.run(task)
    return coder.get_changes()
```

#### Cost Model
Depends on chosen model:
- GPT-4 Turbo: ~$0.01-0.03/request
- Claude Sonnet: ~$3/MTok input, $15/MTok output

---

### 3. Goose ⭐ OPEN-SOURCE POWERHOUSE

**Website:** https://block.github.io/goose
**GitHub:** https://github.com/block/goose
**Maintainer:** Block (formerly Square)

#### Overview
Open-source, extensible AI agent that runs locally. Written in Rust (59%) + TypeScript (34%). 22k stars, Apache 2.0 license.

#### Key Features

✅ **Multi-LLM Support:** Anthropic, OpenAI, Gemini, local models
✅ **Local Execution:** Runs on your machine, no cloud dependencies
✅ **MCP Integration:** Connects to Model Context Protocol servers
✅ **Desktop + CLI:** Both GUI and terminal interfaces
✅ **Autonomous:** Builds projects from scratch, writes/executes code, debugs

#### Installation
```bash
# Unix/macOS
curl -fsSL https://block.github.io/goose/install.sh | sh

# Windows PowerShell
irm https://block.github.io/goose/install.ps1 | iex
```

#### CLI Usage
```bash
goose session start "Build a React login component"
goose run --recipe recipe.yaml
```

#### Configuration
- **Recipe-based:** `recipe.yaml` for task definitions
- **Hints:** `.goosehints` files for context
- **Multi-model:** Configure different LLMs per task

#### Programmatic Integration

The GitHub page shows Python support (2.4% of codebase) but specific Python API docs weren't in the extracted content. Likely controllable via:

1. **CLI Automation:** Shell out to `goose` command
2. **Recipe Files:** Generate YAML configs programmatically
3. **Potential Python Bindings:** Need to explore `goose/` Python modules

#### Integration Strategy for ob1

**Option A: CLI Wrapper**
```python
import subprocess
import json

async def run_goose_agent(task: str, workspace: str):
    result = subprocess.run(
        ["goose", "session", "start", task],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    return parse_goose_output(result.stdout)
```

**Option B: Recipe-based**
```python
import yaml

def create_goose_recipe(task: str, workspace: str):
    recipe = {
        "task": task,
        "workspace": workspace,
        "model": "claude-sonnet-4-5"
    }

    recipe_path = f"{workspace}/goose-recipe.yaml"
    with open(recipe_path, 'w') as f:
        yaml.dump(recipe, f)

    subprocess.run(["goose", "run", "--recipe", recipe_path])
```

#### Strengths for ob1
- **Open Source:** Can fork/modify if needed
- **Active Community:** 322 contributors, Discord support
- **Rust Performance:** Fast execution
- **Flexible LLMs:** Not locked to one provider

#### Limitations
- **Less Documentation:** Newer project, docs still evolving
- **Python API Unclear:** May need CLI wrapper approach

---

### 4. GitHub Copilot CLI ⭐ ENTERPRISE-READY

**Docs:** https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli
**Maintainer:** GitHub/Microsoft

#### Overview
Terminal-native AI agent with deep GitHub integration. Available to all Copilot subscribers (Individual, Business, Enterprise).

#### Installation
```bash
npm install -g @github/copilot
gh auth login  # Authenticate with GitHub
```

#### Programmatic Mode

**Single Prompt:**
```bash
gh copilot --prompt "fix linting errors" --allow-all-tools
```

**Flags for Automation:**
- `-p/--prompt`: Direct prompt (no interactive mode)
- `--allow-all-tools`: Auto-approve all tool usage
- `--allow-tool <name>`: Approve specific tools

#### Key Features

✅ **GitHub Integration:** Access to repos, issues, PRs via natural language
✅ **Programmatic Mode:** Designed for CI/CD and automation
✅ **Enterprise Governance:** Inherits org policies
✅ **No Separate API Key:** Uses existing GitHub credentials

#### Strengths for ob1
- **Zero Setup:** Works if user has Copilot subscription
- **Compliance:** Enterprise-grade security/policies
- **Git Workflows:** Native understanding of GitHub

#### Limitations

⚠️ **No REST API:** CLI is the programmatic interface
⚠️ **Subscription Required:** Not free
⚠️ **Less Autonomous:** More interactive than Claude/Aider

#### Integration Example
```python
import subprocess

async def run_copilot_agent(task: str, workspace: str):
    result = subprocess.run(
        ["gh", "copilot", "--prompt", task, "--allow-all-tools"],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    return result.stdout
```

---

### 5. Cursor CLI 🔬 EXPERIMENTAL

**Website:** https://cursor.com
**Community:** https://forum.cursor.com

#### Overview
AI-first IDE (fork of VS Code) with powerful agent. CLI recently launched for terminal/headless usage.

#### Installation
```bash
# Installation method unclear - likely part of Cursor IDE
# Check: cursor.com/cli or via IDE settings
```

#### Programmatic Access

**Current Status (2025):**
- ✅ **CLI Available:** `cursor-agent` command
- ✅ **Non-interactive Mode:** Print mode for scripts (`-p` flag)
- ✅ **Headless Support:** Designed for CI/CD
- ⚠️ **No Official API:** Community requesting REST API

**Usage Patterns:**
```bash
# Interactive TUI
cursor-agent

# Non-interactive (print mode)
cursor-agent -p -m gpt-5 "find and fix performance issues"

# Output formats
cursor-agent -p --format json "analyze code"
cursor-agent -p --format stream-json "refactor module"
```

#### Community Requests

Active forum discussions about:
- API for headless control
- Programmatic query access with full repo context
- Integration with external tools

#### Integration Strategy for ob1

**AgentAPI Route (Recommended):**
Cursor CLI is supported by AgentAPI, providing standardized HTTP interface.

```python
# Via AgentAPI
async def run_cursor_via_agentapi(task: str):
    response = await httpx.post(
        "http://localhost:3284/message",
        json={"content": task, "type": "user"}
    )
    return response.json()
```

**Direct CLI (If Available):**
```python
async def run_cursor_agent(task: str, workspace: str):
    result = subprocess.run(
        ["cursor-agent", "-p", "-m", "gpt-5", task],
        cwd=workspace,
        capture_output=True,
        text=True
    )
    return result.stdout
```

#### Limitations
- **Unclear Installation:** Documentation sparse
- **No Official API:** CLI-only for now
- **Rapid Evolution:** Features changing quickly

---

### 6. GPT-Engineer 🛠️ GREENFIELD SPECIALIST

**GitHub:** https://github.com/AntonOsika/gpt-engineer
**Maintainer:** Anton Osika

#### Overview
CLI platform for code generation experiments. Optimized for building projects from scratch (vs editing existing code).

#### Installation
```bash
pip install gpt-engineer
```

#### Key Features

✅ **Greenfield Projects:** Best for new codebases
✅ **Multi-Model:** OpenAI, Anthropic, Azure, WizardCoder
✅ **Vision Support:** Can accept architecture diagrams as input
✅ **Custom Preprompts:** Define agent identity/behavior

#### Usage
```bash
gpt-engineer <project-directory> --prompt "Build a todo app"
```

#### Strengths for ob1
- Great for "build from scratch" tasks
- Simple CLI interface
- Active community

#### Limitations
- Less mature than Aider for existing code
- Primarily focused on greenfield
- Smaller ecosystem than Claude/Copilot

---

### 7. Other Notable Agents

#### Sourcegraph Cody ⚡ LARGE CODEBASE CHAMPION

**Website:** https://sourcegraph.com/cody
**Best For:** Monorepos, enterprise codebases

**Key Features:**
- **2M+ lines of context** (Cody Pro 2025)
- Repo-scale reasoning
- Cross-file understanding
- Enterprise-grade security

**Integration:** VS Code, JetBrains, CLI available
**Cost:** Freemium + Pro tier

#### Tabnine 🔒 PRIVACY-FIRST

**Website:** https://tabnine.com
**Best For:** Compliance-heavy orgs, on-prem deployment

**Key Features:**
- **Fully on-prem deployable** (air-gapped)
- Trained only on permissively licensed code
- Fast inline suggestions
- Private fine-tuned models

**Limitations:** Less architectural understanding than Cody

#### Amazon CodeWhisperer ☁️ AWS-NATIVE

**Website:** https://aws.amazon.com/codewhisperer

**Key Features:**
- Deep AWS service integration
- Security scanning (15 languages)
- Reference tracking (flags open-source matches)
- CodeCatalyst pipeline integration

**Best For:** AWS-centric shops

#### Sweep AI 🤖 PR AUTOMATION

**What It Does:** Automated pull request generation from issues
**Status:** Inspired many alternatives (GitHub Copilot Enterprise, Cody Pro)
**Best For:** Issue-to-PR workflows

---

## 🔧 AgentAPI: The Universal Orchestration Layer

**GitHub:** https://github.com/coder/agentapi
**Purpose:** Unified HTTP API for controlling ANY coding agent

### Supported Agents (2025)

- Claude Code
- Goose
- Aider
- GitHub Copilot CLI
- Gemini
- Cursor CLI
- Sourcegraph Amp
- OpenAI Codex
- AmazonQ
- Auggie
- Opencode

### Architecture

AgentAPI acts as an **in-memory terminal emulator** that:
1. Translates HTTP requests → terminal keystrokes
2. Parses agent terminal output → structured JSON
3. Separates user input from agent responses
4. Removes UI artifacts (spinners, colors, etc.)

### HTTP API

#### Start Server
```bash
agentapi server -- claude
agentapi server -- aider --model sonnet --api-key anthropic=sk-ant-...
agentapi server -- goose
```

**Default Port:** 3284
**Docs:** http://localhost:3284/docs

#### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/messages` | GET | Retrieve conversation history |
| `/message` | POST | Send user input to agent |
| `/status` | GET | Check if agent is "stable" or "running" |
| `/events` | GET | Server-Sent Events stream |

#### Example Usage

**Send Message:**
```bash
curl -X POST http://localhost:3284/message \
  -H "Content-Type: application/json" \
  -d '{"content": "Build a login page", "type": "user"}'
```

**Check Status:**
```bash
curl http://localhost:3284/status
# Returns: {"status": "running"} or {"status": "stable"}
```

**Get Messages:**
```bash
curl http://localhost:3284/messages
```

### Security

**Allowed Hosts:**
```bash
agentapi server --allowed-hosts 'example.com,localhost' -- claude
```

**CORS:**
```bash
agentapi server --allowed-origins 'https://app.example.com' -- aider
```

### Integration with ob1

**Perfect for Future Extension:**

```python
import httpx

class AgentAPIClient:
    def __init__(self, port: int = 3284):
        self.base_url = f"http://localhost:{port}"

    async def send_message(self, content: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/message",
                json={"content": content, "type": "user"}
            )
            return response.json()

    async def wait_for_completion(self):
        while True:
            status = await self.get_status()
            if status == "stable":
                break
            await asyncio.sleep(1)

    async def get_status(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/status")
            return response.json()["status"]

    async def get_messages(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/messages")
            return response.json()

# Usage in ob1
async def run_agent_via_agentapi(agent_type: str, task: str, workspace: str):
    # Start AgentAPI server for this agent (subprocess)
    proc = subprocess.Popen([
        "agentapi", "server", "--", agent_type, "--cwd", workspace
    ])

    await asyncio.sleep(2)  # Wait for server startup

    client = AgentAPIClient()
    await client.send_message(task)
    await client.wait_for_completion()
    messages = await client.get_messages()

    proc.terminate()
    return messages
```

### Benefits for ob1

✅ **Unified Interface:** Same API for 10+ agents
✅ **Easy Agent Swapping:** Change agent without code changes
✅ **Future-Proof:** New agents automatically supported
✅ **Agent-to-Agent Communication:** One agent can control another

---

## 📊 Comparison Matrix

| Agent | Headless | Python API | CLI | Multi-LLM | Cost | Open Source | Best For |
|-------|----------|------------|-----|-----------|------|-------------|----------|
| **Claude Agent SDK** | ✅ | ✅ Official | ✅ | ❌ Claude only | $$$ | ❌ | Complex autonomous tasks |
| **Aider** | ✅ | ✅ Unofficial | ✅ | ✅ | $ - $$$ | ✅ | Editing existing code |
| **Goose** | ✅ | ⚠️ Unclear | ✅ | ✅ | $ - $$$ | ✅ | Local, open-source, multi-LLM |
| **Copilot CLI** | ✅ | ❌ | ✅ | ❌ GPT only | $$ | ❌ | GitHub integration |
| **Cursor CLI** | ✅ | ❌ | ✅ | ⚠️ | $$$ | ❌ | IDE-level context |
| **GPT-Engineer** | ✅ | ⚠️ | ✅ | ✅ | $ - $$$ | ✅ | Greenfield projects |
| **Cody** | ⚠️ | ❌ | ✅ | ✅ | $$ | ❌ | Large codebases (2M+ LOC) |
| **Tabnine** | ⚠️ | ❌ | ⚠️ | ✅ | $$$ | ❌ | On-prem, compliance |
| **CodeWhisperer** | ⚠️ | ❌ | ⚠️ | ❌ | $$ | ❌ | AWS ecosystems |

**Legend:**
- ✅ = Full support
- ⚠️ = Partial/experimental
- ❌ = Not available/not applicable
- Cost: $ (cheap) → $$$ (expensive)

---

## 🎯 Recommendations for ob1 Architecture

### Phase 1: MVP (Current)

**Implement These 3 Agents:**

1. **Claude Agent SDK** (Primary)
   - Reason: Best quality, official support, full Python API
   - Use for: Complex multi-file tasks

2. **Aider** (Secondary)
   - Reason: Excellent for focused edits, mature, fast
   - Use for: Surgical code modifications

3. **Goose** (Tertiary)
   - Reason: Open-source, community-driven, multi-LLM
   - Use for: Demonstrating flexibility

### Phase 2: AgentAPI Integration

**Add Unified Interface:**

```python
# ob1/agents/agentapi_adapter.py
class AgentAPIAdapter(Agent):
    """Adapter to run ANY agent via AgentAPI"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type  # "claude", "aider", "cursor", etc.

    async def execute(self, task: str, workspace: str, branch: str) -> AgentResult:
        # Start AgentAPI server
        # Send task
        # Wait for completion
        # Return standardized result
        pass
```

This enables:
- ✅ Easy addition of Cursor, Copilot, Cody, etc.
- ✅ Agent comparison benchmarks
- ✅ User choice of preferred agent

### Phase 3: Intelligent Routing

**Route tasks to best agent:**

```python
class IntelligentOrchestrator:
    def select_agent(self, task: str) -> str:
        if "refactor existing" in task.lower():
            return "aider"  # Best for edits
        elif "build from scratch" in task.lower():
            return "gpt-engineer"  # Best for greenfield
        elif "aws" in task.lower():
            return "codewhisperer"  # AWS native
        else:
            return "claude"  # Default powerhouse
```

---

## 🚀 Demo Script for Stakeholders

**Impressive Features to Highlight:**

### 1. Multi-Agent Parallel Execution
```bash
ob1 -m "Build a React login component" -k 5 \
    --agents claude,aider,goose,copilot,cursor
```

**Output:** 5 PRs from 5 different agents, same task, different approaches

### 2. Agent Comparison Dashboard

```
╭──────────────────────────────────────────────────╮
│           ob1 Execution Summary                  │
├──────────────────────────────────────────────────┤
│ Task: "Build React login component"              │
│ Agents: 5                                        │
│ Success: 5/5                                     │
│ Total Time: 120s                                 │
│ Total Cost: $0.87                                │
├──────────────────────────────────────────────────┤
│ Agent Performance:                               │
│ ✓ Claude Agent  │ 45s │ $0.24 │ PR #123         │
│ ✓ Aider         │ 30s │ $0.12 │ PR #124         │
│ ✓ Goose         │ 52s │ $0.18 │ PR #125         │
│ ✓ Copilot       │ 38s │ $0.21 │ PR #126         │
│ ✓ Cursor        │ 67s │ $0.32 │ PR #127         │
╰──────────────────────────────────────────────────╯
```

### 3. Extensibility Showcase

**Add New Agent in 5 Lines:**

```python
# ob1/agents/new_agent.py
class MyCustomAgent(Agent):
    async def execute(self, task, workspace, branch):
        # Your integration here
        return AgentResult(...)
```

### 4. AgentAPI Integration

**Control 10+ Agents Through One Interface:**

```bash
# Start any agent via AgentAPI
ob1 --use-agentapi --agents cursor,cody,tabnine -k 3
```

---

## 📈 Market Differentiation

### What Makes ob1 Unique?

| Feature | ob1 | Individual Agents |
|---------|-----|-------------------|
| **Parallel Execution** | ✅ Run 5+ agents simultaneously | ❌ One at a time |
| **Agent Comparison** | ✅ Compare output quality | ❌ Manual testing |
| **Multi-Provider** | ✅ Claude, GPT, Gemini, etc. | ❌ Locked to one |
| **Automated PRs** | ✅ All agents create PRs | ⚠️ Manual PR creation |
| **Cost Tracking** | ✅ Aggregate across agents | ⚠️ Per-agent only |
| **AgentAPI Support** | ✅ 10+ agents via HTTP | ❌ N/A |

### Use Cases

1. **A/B Testing Code Solutions**
   - Run 3 agents on same task
   - Pick best PR
   - Merge winner

2. **Redundancy & Quality**
   - If one agent fails, others succeed
   - Higher overall reliability

3. **Agent Benchmarking**
   - Compare speed, cost, quality
   - Data-driven agent selection

4. **Team Collaboration**
   - Different team members prefer different agents
   - ob1 supports all preferences

---

## 🔗 Key Resources

### Official Documentation
- [Claude Agent SDK](https://docs.claude.com/en/docs/agent-sdk/overview)
- [Aider Docs](https://aider.chat/docs/)
- [Goose Docs](https://block.github.io/goose/)
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli)
- [AgentAPI](https://github.com/coder/agentapi)

### GitHub Repositories
- [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- [Aider](https://github.com/Aider-AI/aider)
- [Goose](https://github.com/block/goose)
- [GPT-Engineer](https://github.com/AntonOsika/gpt-engineer)

### Community
- [Cursor Forum](https://forum.cursor.com)
- [Aider GitHub Discussions](https://github.com/Aider-AI/aider/discussions)
- [Goose Discord](https://discord.gg/goose-oss)

---

## ✅ Next Steps for ob1

### Immediate (MVP Demo)

1. ✅ **Implement Claude Agent SDK integration**
   - Use official Python API
   - Full headless operation
   - Cost tracking

2. ✅ **Add Aider as second agent**
   - Python API integration
   - Headless mode with `--yes`
   - Demonstrate multi-agent orchestration

3. ✅ **Create impressive demo**
   - 3 agents, 3 PRs
   - Rich terminal output
   - Performance metrics

### Short-term (Post-MVP)

4. **Add Goose integration**
   - CLI wrapper or Python bindings
   - Showcase open-source option

5. **Build AgentAPI adapter**
   - Unified interface for future agents
   - Easy expansion

### Long-term (Production)

6. **Intelligent agent routing**
   - Task analysis
   - Best-fit agent selection

7. **Agent comparison dashboard**
   - Web UI for results
   - Quality scoring

8. **Custom agent marketplace**
   - User-contributed agents
   - Plugin system

---

## 💡 Key Insights

1. **AgentAPI is the secret weapon** - It unlocks 10+ agents with minimal integration effort

2. **Claude Agent SDK + Aider = Powerful Combo** - Claude for complex tasks, Aider for edits

3. **Python 3.10+ requirement** - Many agents need this (Claude SDK, Goose)

4. **Cost tracking matters** - Users want to see $/agent for budgeting

5. **Parallel execution is differentiator** - No other tool orchestrates multiple agents simultaneously

6. **PR quality varies** - Some agents better for certain tasks (routing logic needed)

---

**End of Research Report**

Generated: January 2025
For: ob1 Parallel AI SWE Orchestrator
Status: Ready for impressive stakeholder demo 🚀
