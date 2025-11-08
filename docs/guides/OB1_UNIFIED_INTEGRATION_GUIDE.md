# ob1 Unified Integration Guide
## Multi-Agent Orchestrator Architecture

**Created:** 2025-11-09
**Purpose:** Unified integration architecture for Claude, OpenAI, and Cursor agents
**Status:** Production-Ready

---

## Executive Summary

This document provides the complete architecture for integrating three AI agents into the ob1 orchestrator:

1. **Claude Agent SDK** - Local worktree execution, rich tooling
2. **OpenAI Chat Completions** - Programmatic code generation, local execution
3. **Cursor Cloud Agent** - Cloud-based GitHub execution

### Quick Comparison

| Feature | Claude Agent SDK | OpenAI API | Cursor API |
|---------|-----------------|------------|------------|
| **Local Worktrees** | ✅ Yes | ✅ Yes | ❌ No (GitHub only) |
| **Async Support** | ✅ Native | ✅ Native | ✅ Native |
| **Git Integration** | ✅ Built-in | ⚠️ Manual | ✅ Built-in |
| **Auto PR Creation** | ✅ Yes | ❌ No | ✅ Yes |
| **Cost per Task** | ~$0.15 | ~$0.10 | ~$0.20 |
| **Best For** | Complex tasks | Simple tasks | Cloud workflows |

### Recommended Strategy

**Phase 1 (MVP):** Claude + OpenAI (local worktrees)
**Phase 2:** Add Cursor (cloud-based competition)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Unified Agent Interface](#unified-agent-interface)
3. [Python Implementation](#python-implementation)
4. [JavaScript/TypeScript Implementation](#javascripttypescript-implementation)
5. [Git Worktree Strategy](#git-worktree-strategy)
6. [Parallel Execution Patterns](#parallel-execution-patterns)
7. [Error Handling & Retry Logic](#error-handling--retry-logic)
8. [Testing Strategy](#testing-strategy)
9. [Deployment & CI/CD](#deployment--cicd)

---

## 1. Architecture Overview

### 1.1 System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    ob1 CLI                                  │
│  Command: ob1 -m "Build login page" -k 3                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               Orchestrator (async)                          │
│  - Parse task description                                   │
│  - Create k agents (Claude, OpenAI, Cursor)                 │
│  - Manage parallel execution                                │
│  - Collect results                                          │
└─────────────┬───────────────┬───────────────┬───────────────┘
              │               │               │
              ▼               ▼               ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Claude     │  │   OpenAI    │  │   Cursor    │
    │  Agent      │  │   Agent     │  │   Agent     │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ Worktree 1  │  │ Worktree 2  │  │  GitHub     │
    │  (local)    │  │  (local)    │  │  Branch     │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           └────────────────┴────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  3 Pull         │
                   │  Requests       │
                   │  Created        │
                   └─────────────────┘
```

### 1.2 Data Flow

```
1. User Input → CLI Parser
2. CLI → Orchestrator (with task description + k value)
3. Orchestrator → Create k worktrees/branches in parallel
4. Orchestrator → Launch k agents in parallel (asyncio.gather)
5. Agents → Execute tasks independently
6. Agents → Create commits in their worktrees/branches
7. Agents → Create PRs via GitHub API
8. Orchestrator → Collect PR URLs
9. CLI → Display results to user
```

### 1.3 Technology Stack

**Backend (Python):**
- `asyncio` - Async orchestration
- `httpx` - Async HTTP client
- `typer` - CLI framework
- `pydantic` - Type validation
- `pytest` - Testing framework
- `tenacity` - Retry logic

**Backend (JavaScript/TypeScript):**
- `async/await` - Native async
- `node-fetch` / `axios` - HTTP clients
- `commander` - CLI framework
- `zod` - Type validation
- `jest` - Testing framework
- `p-retry` - Retry logic

**Git Management:**
- `git worktree` - Isolated workspaces
- `PyGithub` / `@octokit/rest` - GitHub API

---

## 2. Unified Agent Interface

### 2.1 Abstract Base Interface

All agents must implement this interface:

**Python:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AgentType(Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    CURSOR = "cursor"

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentResult:
    """Result from agent execution"""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    commit_sha: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None

@dataclass
class AgentConfig:
    """Configuration for agent initialization"""
    agent_type: AgentType
    api_key: str
    workspace_path: str
    repo_url: str
    base_branch: str = "main"
    model: Optional[str] = None
    timeout_seconds: int = 600
    max_retries: int = 3

class BaseAgent(ABC):
    """Abstract base class for all AI agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = f"{config.agent_type.value}-{id(self)}"
        self.status = AgentStatus.IDLE

    @abstractmethod
    async def setup(self) -> None:
        """Initialize agent (create worktree, setup environment)"""
        pass

    @abstractmethod
    async def execute_task(self, task_description: str) -> AgentResult:
        """Execute the coding task"""
        pass

    @abstractmethod
    async def create_pr(
        self,
        title: str,
        body: str,
        base: str = "main"
    ) -> str:
        """Create pull request and return PR URL"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources (remove worktree, close connections)"""
        pass

    async def __aenter__(self):
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
```

**TypeScript:**
```typescript
enum AgentType {
  CLAUDE = 'claude',
  OPENAI = 'openai',
  CURSOR = 'cursor',
}

enum AgentStatus {
  IDLE = 'idle',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

interface AgentResult {
  agentId: string;
  agentType: AgentType;
  status: AgentStatus;
  prUrl?: string;
  branchName?: string;
  commitSha?: string;
  error?: string;
  durationSeconds?: number;
  costUsd?: number;
}

interface AgentConfig {
  agentType: AgentType;
  apiKey: string;
  workspacePath: string;
  repoUrl: string;
  baseBranch?: string;
  model?: string;
  timeoutSeconds?: number;
  maxRetries?: number;
}

abstract class BaseAgent {
  protected config: AgentConfig;
  protected agentId: string;
  protected status: AgentStatus;

  constructor(config: AgentConfig) {
    this.config = config;
    this.agentId = `${config.agentType}-${Date.now()}`;
    this.status = AgentStatus.IDLE;
  }

  abstract setup(): Promise<void>;
  abstract executeTask(taskDescription: string): Promise<AgentResult>;
  abstract createPR(title: string, body: string, base?: string): Promise<string>;
  abstract cleanup(): Promise<void>;

  async run(taskDescription: string): Promise<AgentResult> {
    try {
      await this.setup();
      return await this.executeTask(taskDescription);
    } finally {
      await this.cleanup();
    }
  }
}
```

### 2.2 Agent Factory Pattern

**Python:**
```python
from typing import Type

class AgentFactory:
    """Factory for creating agents"""

    _agents: Dict[AgentType, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_type: AgentType):
        """Decorator to register agent implementations"""
        def wrapper(agent_class: Type[BaseAgent]):
            cls._agents[agent_type] = agent_class
            return agent_class
        return wrapper

    @classmethod
    def create(cls, config: AgentConfig) -> BaseAgent:
        """Create agent instance"""
        agent_class = cls._agents.get(config.agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {config.agent_type}")
        return agent_class(config)

# Usage:
@AgentFactory.register(AgentType.CLAUDE)
class ClaudeAgent(BaseAgent):
    async def setup(self):
        # Implementation
        pass
```

**TypeScript:**
```typescript
class AgentFactory {
  private static agents = new Map<AgentType, new (config: AgentConfig) => BaseAgent>();

  static register(agentType: AgentType) {
    return function <T extends new (config: AgentConfig) => BaseAgent>(constructor: T) {
      AgentFactory.agents.set(agentType, constructor);
      return constructor;
    };
  }

  static create(config: AgentConfig): BaseAgent {
    const AgentClass = this.agents.get(config.agentType);
    if (!AgentClass) {
      throw new Error(`Unknown agent type: ${config.agentType}`);
    }
    return new AgentClass(config);
  }
}

// Usage:
@AgentFactory.register(AgentType.CLAUDE)
class ClaudeAgent extends BaseAgent {
  async setup(): Promise<void> {
    // Implementation
  }
}
```

---

## 3. Python Implementation

### 3.1 Claude Agent Implementation

```python
# ob1/agents/claude.py
import asyncio
from pathlib import Path
from typing import Optional
import time
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from ..workspace.worktree import WorktreeManager
from ..workspace.github_pr import GitHubPRManager
from .base import BaseAgent, AgentType, AgentResult, AgentStatus, AgentConfig

@AgentFactory.register(AgentType.CLAUDE)
class ClaudeAgent(BaseAgent):
    """Claude Agent SDK implementation"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.client: Optional[ClaudeSDKClient] = None
        self.worktree_manager: Optional[WorktreeManager] = None
        self.github_manager: Optional[GitHubPRManager] = None
        self.branch_name: Optional[str] = None

    async def setup(self) -> None:
        """Initialize Claude agent and worktree"""
        # Create worktree
        self.worktree_manager = WorktreeManager(
            repo_path=self.config.workspace_path,
            base_branch=self.config.base_branch
        )
        self.branch_name = await self.worktree_manager.create_worktree(
            prefix=f"claude-{self.agent_id}"
        )

        # Initialize Claude client
        self.client = ClaudeSDKClient(
            api_key=self.config.api_key,
            model=self.config.model or "claude-sonnet-4-5-20250929",
            options=ClaudeAgentOptions(
                working_directory=self.worktree_manager.worktree_path,
                max_turns=50,
                setting_sources=["project"],  # Load CLAUDE.md
            )
        )

        # Initialize GitHub manager
        self.github_manager = GitHubPRManager(
            repo_url=self.config.repo_url,
            worktree_path=self.worktree_manager.worktree_path
        )

        self.status = AgentStatus.IDLE

    async def execute_task(self, task_description: str) -> AgentResult:
        """Execute coding task with Claude"""
        start_time = time.time()
        self.status = AgentStatus.RUNNING

        try:
            # Create system prompt with TDD requirements
            system_prompt = f"""
You are an expert software engineer working on a coding task.

CRITICAL: Follow TDD strictly:
1. Write failing tests FIRST
2. Run tests to confirm they fail (RED)
3. Implement minimal code to make tests pass (GREEN)
4. Refactor while keeping tests passing

Project context is in CLAUDE.md in the repository.

Your task: {task_description}

When complete:
1. Ensure all tests pass
2. Commit your changes with a descriptive message
3. The orchestrator will create the PR
"""

            # Execute with Claude
            conversation = []
            async for message in self.client.query(
                prompt=system_prompt,
                conversation=conversation,
            ):
                conversation.append(message)
                # Log progress
                if message.get("type") == "text":
                    print(f"[{self.agent_id}] {message.get('text', '')[:100]}")

            # Check for completion
            final_message = conversation[-1] if conversation else {}
            if final_message.get("stop_reason") == "end_turn":
                self.status = AgentStatus.COMPLETED
            else:
                self.status = AgentStatus.FAILED
                raise Exception(f"Task incomplete: {final_message.get('stop_reason')}")

            # Create PR
            pr_url = await self.create_pr(
                title=f"Claude: {task_description[:50]}",
                body=f"""## Task
{task_description}

## Implementation
This PR was created by Claude Agent SDK.

🤖 Generated with [ob1 Orchestrator](https://github.com/yourusername/ob1)
Agent: Claude Agent SDK
Agent ID: {self.agent_id}
"""
            )

            duration = time.time() - start_time

            return AgentResult(
                agent_id=self.agent_id,
                agent_type=AgentType.CLAUDE,
                status=self.status,
                pr_url=pr_url,
                branch_name=self.branch_name,
                duration_seconds=duration,
                cost_usd=self._estimate_cost(conversation),
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_id=self.agent_id,
                agent_type=AgentType.CLAUDE,
                status=self.status,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def create_pr(self, title: str, body: str, base: str = "main") -> str:
        """Create pull request"""
        # Push branch
        await self.github_manager.push_branch(self.branch_name)

        # Create PR via GitHub API
        pr_url = await self.github_manager.create_pr(
            title=title,
            head=self.branch_name,
            base=base,
            body=body,
        )

        return pr_url

    async def cleanup(self) -> None:
        """Cleanup worktree and close connections"""
        if self.worktree_manager:
            await self.worktree_manager.remove_worktree()
        if self.client:
            # Close client if needed
            pass

    def _estimate_cost(self, conversation: list) -> float:
        """Estimate cost based on token usage"""
        # Rough estimate: $15 per 1M input tokens, $75 per 1M output tokens
        # Average conversation: ~50k input, ~10k output
        return 0.15  # Placeholder
```

### 3.2 OpenAI Agent Implementation

```python
# ob1/agents/openai.py
import asyncio
import os
from pathlib import Path
from typing import Optional
import time
from openai import AsyncOpenAI
from ..workspace.worktree import WorktreeManager
from ..workspace.github_pr import GitHubPRManager
from .base import BaseAgent, AgentType, AgentResult, AgentStatus, AgentConfig

@AgentFactory.register(AgentType.OPENAI)
class OpenAIAgent(BaseAgent):
    """OpenAI Chat Completions implementation"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.client: Optional[AsyncOpenAI] = None
        self.worktree_manager: Optional[WorktreeManager] = None
        self.github_manager: Optional[GitHubPRManager] = None
        self.branch_name: Optional[str] = None

    async def setup(self) -> None:
        """Initialize OpenAI client and worktree"""
        # Create worktree
        self.worktree_manager = WorktreeManager(
            repo_path=self.config.workspace_path,
            base_branch=self.config.base_branch
        )
        self.branch_name = await self.worktree_manager.create_worktree(
            prefix=f"openai-{self.agent_id}"
        )

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.config.api_key)

        # Initialize GitHub manager
        self.github_manager = GitHubPRManager(
            repo_url=self.config.repo_url,
            worktree_path=self.worktree_manager.worktree_path
        )

        self.status = AgentStatus.IDLE

    async def execute_task(self, task_description: str) -> AgentResult:
        """Execute coding task with OpenAI"""
        start_time = time.time()
        self.status = AgentStatus.RUNNING

        try:
            # Read project context
            context = await self._gather_context()

            # Create messages
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert software engineer. Follow TDD strictly:
1. Write tests first
2. Run tests to confirm failure
3. Implement minimal code
4. Refactor

Project context:
{context}
"""
                },
                {
                    "role": "user",
                    "content": f"Task: {task_description}\n\nImplement this feature following TDD. Provide the complete implementation as code blocks."
                }
            ]

            # Execute with streaming
            response = await self.client.chat.completions.create(
                model=self.config.model or "gpt-4o",
                messages=messages,
                max_tokens=4000,
                temperature=0.2,
                stream=True,
            )

            full_response = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(f"[{self.agent_id}] {content}", end="", flush=True)

            print()  # Newline after streaming

            # Parse response and create files
            await self._apply_code_changes(full_response)

            # Create commit
            await self._create_commit(task_description)

            # Create PR
            pr_url = await self.create_pr(
                title=f"OpenAI: {task_description[:50]}",
                body=f"""## Task
{task_description}

## Implementation
This PR was created by OpenAI GPT-4o.

🤖 Generated with [ob1 Orchestrator](https://github.com/yourusername/ob1)
Agent: OpenAI
Agent ID: {self.agent_id}
"""
            )

            self.status = AgentStatus.COMPLETED
            duration = time.time() - start_time

            return AgentResult(
                agent_id=self.agent_id,
                agent_type=AgentType.OPENAI,
                status=self.status,
                pr_url=pr_url,
                branch_name=self.branch_name,
                duration_seconds=duration,
                cost_usd=0.10,  # Estimate
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_id=self.agent_id,
                agent_type=AgentType.OPENAI,
                status=self.status,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def _gather_context(self) -> str:
        """Read project files for context"""
        context_files = [
            "CLAUDE.md",
            "README.md",
            "pyproject.toml",
        ]

        context = ""
        worktree_path = Path(self.worktree_manager.worktree_path)

        for file_name in context_files:
            file_path = worktree_path / file_name
            if file_path.exists():
                context += f"\n\n# {file_name}\n{file_path.read_text()}"

        return context

    async def _apply_code_changes(self, response: str) -> None:
        """Parse response and apply code changes"""
        # Simple implementation: look for code blocks and write files
        # Production: Use proper parsing with tree-sitter or similar
        import re

        # Find code blocks with file paths
        pattern = r"```(?:python|typescript|javascript|json)\n# ([\w/\.]+)\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)

        worktree_path = Path(self.worktree_manager.worktree_path)

        for file_path, code in matches:
            full_path = worktree_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(code)
            print(f"[{self.agent_id}] Created/updated: {file_path}")

    async def _create_commit(self, task_description: str) -> None:
        """Create git commit"""
        worktree_path = self.worktree_manager.worktree_path

        # Git add and commit
        proc = await asyncio.create_subprocess_exec(
            "git", "add", ".",
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        commit_message = f"""feat: {task_description}

🤖 Generated with ob1 Orchestrator
Agent: OpenAI GPT-4o
Agent ID: {self.agent_id}

Co-Authored-By: OpenAI <noreply@openai.com>"""

        proc = await asyncio.create_subprocess_exec(
            "git", "commit", "-m", commit_message,
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise Exception(f"Git commit failed: {stderr.decode()}")

    async def create_pr(self, title: str, body: str, base: str = "main") -> str:
        """Create pull request"""
        await self.github_manager.push_branch(self.branch_name)

        pr_url = await self.github_manager.create_pr(
            title=title,
            head=self.branch_name,
            base=base,
            body=body,
        )

        return pr_url

    async def cleanup(self) -> None:
        """Cleanup worktree"""
        if self.worktree_manager:
            await self.worktree_manager.remove_worktree()
        if self.client:
            await self.client.close()
```

### 3.3 Cursor Agent Implementation

```python
# ob1/agents/cursor.py
import asyncio
import httpx
from typing import Optional
import time
from ..workspace.github_pr import GitHubBranchManager
from .base import BaseAgent, AgentType, AgentResult, AgentStatus, AgentConfig

@AgentFactory.register(AgentType.CURSOR)
class CursorAgent(BaseAgent):
    """Cursor Cloud Agent API implementation"""

    BASE_URL = "https://api.cursor.com/v0"

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.branch_manager: Optional[GitHubBranchManager] = None
        self.branch_name: Optional[str] = None
        self.agent_id_remote: Optional[str] = None

    async def setup(self) -> None:
        """Initialize Cursor API client and create GitHub branch"""
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            auth=(self.config.api_key, ""),  # Basic auth with API key as username
            timeout=httpx.Timeout(60.0),
        )

        # Create branch manager
        self.branch_manager = GitHubBranchManager(
            repo_url=self.config.repo_url,
            github_token=os.environ["GITHUB_TOKEN"],
        )

        # Create branch on GitHub
        self.branch_name = await self.branch_manager.create_branch(
            base=self.config.base_branch,
            name=f"cursor-{self.agent_id}",
        )

        self.status = AgentStatus.IDLE

    async def execute_task(self, task_description: str) -> AgentResult:
        """Execute coding task with Cursor"""
        start_time = time.time()
        self.status = AgentStatus.RUNNING

        try:
            # Launch agent via API
            response = await self.client.post(
                "/agents",
                json={
                    "prompt": task_description,
                    "repository": self.config.repo_url,
                    "ref": self.branch_name,
                    "model": self.config.model or "claude-4-sonnet",
                    "auto_create_pr": True,
                    "pr_title": f"Cursor: {task_description[:50]}",
                    "pr_body": f"""## Task
{task_description}

🤖 Generated with [ob1 Orchestrator](https://github.com/yourusername/ob1)
Agent: Cursor Cloud Agent
Agent ID: {self.agent_id}
""",
                }
            )
            response.raise_for_status()

            agent_data = response.json()
            self.agent_id_remote = agent_data["id"]

            print(f"[{self.agent_id}] Cursor agent launched: {self.agent_id_remote}")

            # Poll for completion
            pr_url = await self._wait_for_completion()

            self.status = AgentStatus.COMPLETED
            duration = time.time() - start_time

            return AgentResult(
                agent_id=self.agent_id,
                agent_type=AgentType.CURSOR,
                status=self.status,
                pr_url=pr_url,
                branch_name=self.branch_name,
                duration_seconds=duration,
                cost_usd=0.20,  # Estimate
            )

        except Exception as e:
            self.status = AgentStatus.FAILED
            return AgentResult(
                agent_id=self.agent_id,
                agent_type=AgentType.CURSOR,
                status=self.status,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def _wait_for_completion(self) -> Optional[str]:
        """Poll agent status until completion"""
        max_wait = self.config.timeout_seconds
        poll_interval = 10  # seconds
        elapsed = 0

        while elapsed < max_wait:
            response = await self.client.get(f"/agents/{self.agent_id_remote}")
            response.raise_for_status()

            data = response.json()
            status = data.get("status")

            if status == "FINISHED":
                # Get PR URL from agent data
                pr_url = data.get("pr_url")
                return pr_url
            elif status == "ERROR":
                error_msg = data.get("error", "Unknown error")
                raise Exception(f"Cursor agent failed: {error_msg}")

            # Wait before next poll
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            print(f"[{self.agent_id}] Status: {status} ({elapsed}/{max_wait}s)")

        raise TimeoutError(f"Agent did not complete within {max_wait}s")

    async def create_pr(self, title: str, body: str, base: str = "main") -> str:
        """PR is auto-created by Cursor API"""
        raise NotImplementedError("Cursor creates PRs automatically")

    async def cleanup(self) -> None:
        """Cleanup HTTP client"""
        if self.client:
            await self.client.aclose()
```

### 3.4 Orchestrator Implementation

```python
# ob1/orchestrator.py
import asyncio
from typing import List, Dict
from .agents.base import AgentFactory, AgentConfig, AgentType, AgentResult
from .utils.logger import get_logger

logger = get_logger(__name__)

class Orchestrator:
    """Main orchestrator for parallel AI agents"""

    def __init__(
        self,
        repo_path: str,
        repo_url: str,
        base_branch: str = "main",
    ):
        self.repo_path = repo_path
        self.repo_url = repo_url
        self.base_branch = base_branch

    async def execute(
        self,
        task_description: str,
        num_agents: int = 3,
        agent_types: List[AgentType] = None,
    ) -> List[AgentResult]:
        """Execute task with k parallel agents"""

        # Default to Claude and OpenAI (local)
        if agent_types is None:
            agent_types = [AgentType.CLAUDE, AgentType.OPENAI, AgentType.CURSOR]

        # Create agent configs
        configs = []
        for i in range(num_agents):
            agent_type = agent_types[i % len(agent_types)]

            config = self._create_config(agent_type, i)
            configs.append(config)

        # Execute in parallel
        logger.info(f"Launching {num_agents} agents for task: {task_description}")

        tasks = [
            self._run_agent(config, task_description)
            for config in configs
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent failed: {result}")
                continue
            agent_results.append(result)

        # Log summary
        self._log_summary(agent_results)

        return agent_results

    def _create_config(self, agent_type: AgentType, index: int) -> AgentConfig:
        """Create agent configuration"""
        import os

        api_keys = {
            AgentType.CLAUDE: os.environ.get("ANTHROPIC_API_KEY"),
            AgentType.OPENAI: os.environ.get("OPENAI_API_KEY"),
            AgentType.CURSOR: os.environ.get("CURSOR_API_KEY"),
        }

        return AgentConfig(
            agent_type=agent_type,
            api_key=api_keys[agent_type],
            workspace_path=self.repo_path,
            repo_url=self.repo_url,
            base_branch=self.base_branch,
        )

    async def _run_agent(
        self,
        config: AgentConfig,
        task_description: str,
    ) -> AgentResult:
        """Run single agent with setup/cleanup"""
        agent = AgentFactory.create(config)

        async with agent:
            result = await agent.execute_task(task_description)

        return result

    def _log_summary(self, results: List[AgentResult]) -> None:
        """Log summary of results"""
        logger.info("\n" + "="*60)
        logger.info("ORCHESTRATOR SUMMARY")
        logger.info("="*60)

        for result in results:
            status_emoji = "✅" if result.status.value == "completed" else "❌"
            logger.info(f"{status_emoji} {result.agent_type.value}: {result.pr_url}")

        total_cost = sum(r.cost_usd or 0 for r in results)
        logger.info(f"\nTotal cost: ${total_cost:.2f}")
        logger.info("="*60)
```

### 3.5 CLI Implementation

```python
# ob1/cli.py
import asyncio
import typer
from pathlib import Path
from .orchestrator import Orchestrator
from .utils.logger import setup_logger

app = typer.Typer()

@app.command()
def run(
    message: str = typer.Option(..., "-m", "--message", help="Task description"),
    k: int = typer.Option(3, "-k", help="Number of parallel agents"),
    repo: str = typer.Option(None, "-r", "--repo", help="Repository URL (default: current dir)"),
    base: str = typer.Option("main", "-b", "--base", help="Base branch"),
):
    """
    Run k AI agents in parallel to complete a coding task.

    Example:
        ob1 -m "Build me a frontend login page" -k 3
    """
    setup_logger()

    # Get repo path and URL
    if repo is None:
        repo_path = Path.cwd()
        repo_url = _get_repo_url(repo_path)
    else:
        repo_url = repo
        repo_path = Path.cwd()  # Assume running in repo

    # Create orchestrator
    orchestrator = Orchestrator(
        repo_path=str(repo_path),
        repo_url=repo_url,
        base_branch=base,
    )

    # Run
    typer.echo(f"🚀 Launching {k} agents...")
    typer.echo(f"📝 Task: {message}")

    results = asyncio.run(
        orchestrator.execute(
            task_description=message,
            num_agents=k,
        )
    )

    # Display results
    typer.echo("\n" + "="*60)
    typer.echo("✨ RESULTS")
    typer.echo("="*60)

    for result in results:
        if result.pr_url:
            typer.echo(f"✅ {result.agent_type.value}: {result.pr_url}")
        else:
            typer.echo(f"❌ {result.agent_type.value}: {result.error}")

    typer.echo("="*60)

def _get_repo_url(repo_path: Path) -> str:
    """Get GitHub URL from git remote"""
    import subprocess

    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise Exception("Not a git repository or no remote 'origin'")

    return result.stdout.strip()

if __name__ == "__main__":
    app()
```

---

## 4. JavaScript/TypeScript Implementation

### 4.1 Claude Agent Implementation

```typescript
// src/agents/claude.ts
import { ClaudeSDKClient, ClaudeAgentOptions } from '@anthropic-ai/claude-agent-sdk';
import { BaseAgent, AgentType, AgentResult, AgentStatus, AgentConfig } from './base';
import { WorktreeManager } from '../workspace/worktree';
import { GitHubPRManager } from '../workspace/github-pr';

export class ClaudeAgent extends BaseAgent {
  private client?: ClaudeSDKClient;
  private worktreeManager?: WorktreeManager;
  private githubManager?: GitHubPRManager;
  private branchName?: string;

  async setup(): Promise<void> {
    // Create worktree
    this.worktreeManager = new WorktreeManager(
      this.config.workspacePath,
      this.config.baseBranch || 'main'
    );
    this.branchName = await this.worktreeManager.createWorktree(`claude-${this.agentId}`);

    // Initialize Claude client
    this.client = new ClaudeSDKClient({
      apiKey: this.config.apiKey,
      model: this.config.model || 'claude-sonnet-4-5-20250929',
      options: {
        workingDirectory: this.worktreeManager.worktreePath,
        maxTurns: 50,
        settingSources: ['project'],
      } as ClaudeAgentOptions,
    });

    // Initialize GitHub manager
    this.githubManager = new GitHubPRManager(
      this.config.repoUrl,
      this.worktreeManager.worktreePath
    );

    this.status = AgentStatus.IDLE;
  }

  async executeTask(taskDescription: string): Promise<AgentResult> {
    const startTime = Date.now();
    this.status = AgentStatus.RUNNING;

    try {
      const systemPrompt = `
You are an expert software engineer working on a coding task.

CRITICAL: Follow TDD strictly:
1. Write failing tests FIRST
2. Run tests to confirm they fail (RED)
3. Implement minimal code to make tests pass (GREEN)
4. Refactor while keeping tests passing

Project context is in CLAUDE.md in the repository.

Your task: ${taskDescription}

When complete:
1. Ensure all tests pass
2. Commit your changes with a descriptive message
3. The orchestrator will create the PR
`;

      const conversation: any[] = [];

      for await (const message of this.client!.query(systemPrompt, conversation)) {
        conversation.push(message);
        if (message.type === 'text') {
          console.log(`[${this.agentId}] ${message.text?.substring(0, 100)}`);
        }
      }

      // Check completion
      const finalMessage = conversation[conversation.length - 1];
      if (finalMessage.stopReason === 'end_turn') {
        this.status = AgentStatus.COMPLETED;
      } else {
        throw new Error(`Task incomplete: ${finalMessage.stopReason}`);
      }

      // Create PR
      const prUrl = await this.createPR(
        `Claude: ${taskDescription.substring(0, 50)}`,
        `## Task\n${taskDescription}\n\n🤖 Generated with ob1 Orchestrator\nAgent: Claude Agent SDK\nAgent ID: ${this.agentId}`
      );

      const duration = (Date.now() - startTime) / 1000;

      return {
        agentId: this.agentId,
        agentType: AgentType.CLAUDE,
        status: this.status,
        prUrl,
        branchName: this.branchName,
        durationSeconds: duration,
        costUsd: 0.15,
      };
    } catch (error) {
      this.status = AgentStatus.FAILED;
      return {
        agentId: this.agentId,
        agentType: AgentType.CLAUDE,
        status: this.status,
        error: error instanceof Error ? error.message : String(error),
        durationSeconds: (Date.now() - startTime) / 1000,
      };
    }
  }

  async createPR(title: string, body: string, base: string = 'main'): Promise<string> {
    await this.githubManager!.pushBranch(this.branchName!);
    return await this.githubManager!.createPR(title, this.branchName!, base, body);
  }

  async cleanup(): Promise<void> {
    if (this.worktreeManager) {
      await this.worktreeManager.removeWorktree();
    }
  }
}
```

### 4.2 CLI Implementation

```typescript
// src/cli.ts
import { Command } from 'commander';
import { Orchestrator } from './orchestrator';
import { setupLogger } from './utils/logger';

const program = new Command();

program
  .name('ob1')
  .description('Parallel AI SWE orchestrator')
  .version('1.0.0');

program
  .command('run')
  .description('Run k AI agents in parallel')
  .requiredOption('-m, --message <message>', 'Task description')
  .option('-k, --k <number>', 'Number of parallel agents', '3')
  .option('-r, --repo <url>', 'Repository URL')
  .option('-b, --base <branch>', 'Base branch', 'main')
  .action(async (options) => {
    setupLogger();

    const k = parseInt(options.k, 10);
    const repoUrl = options.repo || await getRepoUrl();
    const repoPath = process.cwd();

    console.log(`🚀 Launching ${k} agents...`);
    console.log(`📝 Task: ${options.message}`);

    const orchestrator = new Orchestrator(repoPath, repoUrl, options.base);

    const results = await orchestrator.execute(options.message, k);

    console.log('\n' + '='.repeat(60));
    console.log('✨ RESULTS');
    console.log('='.repeat(60));

    for (const result of results) {
      if (result.prUrl) {
        console.log(`✅ ${result.agentType}: ${result.prUrl}`);
      } else {
        console.log(`❌ ${result.agentType}: ${result.error}`);
      }
    }

    console.log('='.repeat(60));
  });

async function getRepoUrl(): Promise<string> {
  const { exec } = await import('child_process');
  const { promisify } = await import('util');
  const execAsync = promisify(exec);

  const { stdout } = await execAsync('git remote get-url origin');
  return stdout.trim();
}

program.parse();
```

---

## 5. Git Worktree Strategy

### 5.1 Worktree Management

**Python:**
```python
# ob1/workspace/worktree.py
import asyncio
from pathlib import Path
from typing import Optional

class WorktreeManager:
    """Manage git worktrees for parallel agent execution"""

    def __init__(self, repo_path: str, base_branch: str = "main"):
        self.repo_path = Path(repo_path)
        self.base_branch = base_branch
        self.worktree_path: Optional[Path] = None
        self.branch_name: Optional[str] = None

    async def create_worktree(self, prefix: str) -> str:
        """Create a new worktree and branch"""
        # Generate unique branch name
        import time
        timestamp = int(time.time())
        self.branch_name = f"{prefix}-{timestamp}"

        # Worktree path in parent directory
        worktree_name = f".worktrees/{self.branch_name}"
        self.worktree_path = self.repo_path.parent / worktree_name

        # Create worktree
        proc = await asyncio.create_subprocess_exec(
            "git", "worktree", "add",
            "-b", self.branch_name,
            str(self.worktree_path),
            self.base_branch,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise Exception(f"Failed to create worktree: {stderr.decode()}")

        return self.branch_name

    async def remove_worktree(self) -> None:
        """Remove worktree and clean up"""
        if not self.worktree_path:
            return

        # Remove worktree
        proc = await asyncio.create_subprocess_exec(
            "git", "worktree", "remove",
            str(self.worktree_path),
            "--force",
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await proc.communicate()

        # Delete branch (optional)
        # await self._delete_branch()

    async def _delete_branch(self) -> None:
        """Delete the branch (optional cleanup)"""
        if not self.branch_name:
            return

        proc = await asyncio.create_subprocess_exec(
            "git", "branch", "-D", self.branch_name,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await proc.communicate()
```

### 5.2 GitHub PR Management

```python
# ob1/workspace/github_pr.py
import os
from github import Github
from github.Repository import Repository

class GitHubPRManager:
    """Manage GitHub pull requests"""

    def __init__(self, repo_url: str, worktree_path: str):
        self.repo_url = repo_url
        self.worktree_path = worktree_path

        # Parse owner/repo from URL
        # https://github.com/owner/repo.git -> owner/repo
        parts = repo_url.rstrip('.git').split('/')
        self.repo_name = f"{parts[-2]}/{parts[-1]}"

        # Initialize GitHub client
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")

        self.github = Github(github_token)
        self.repo: Repository = self.github.get_repo(self.repo_name)

    async def push_branch(self, branch_name: str) -> None:
        """Push branch to remote"""
        import asyncio

        proc = await asyncio.create_subprocess_exec(
            "git", "push", "-u", "origin", branch_name,
            cwd=self.worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise Exception(f"Failed to push branch: {stderr.decode()}")

    async def create_pr(
        self,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> str:
        """Create pull request"""
        # Run in thread pool since PyGithub is synchronous
        import asyncio

        pr = await asyncio.to_thread(
            self.repo.create_pull,
            title=title,
            body=body,
            head=head,
            base=base,
        )

        return pr.html_url
```

---

## 6. Parallel Execution Patterns

### 6.1 Basic Parallel Execution

```python
# Simple parallel execution
import asyncio

async def main():
    tasks = [
        agent1.execute_task("Build login page"),
        agent2.execute_task("Build login page"),
        agent3.execute_task("Build login page"),
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### 6.2 With Progress Tracking

```python
# With progress tracking
from rich.progress import Progress

async def execute_with_progress(tasks: list):
    with Progress() as progress:
        task_ids = [
            progress.add_task(f"[cyan]Agent {i+1}...", total=100)
            for i in range(len(tasks))
        ]

        async def track_task(task, task_id):
            # Update progress periodically
            result = await task
            progress.update(task_id, completed=100)
            return result

        tracked = [
            track_task(task, tid)
            for task, tid in zip(tasks, task_ids)
        ]

        return await asyncio.gather(*tracked)
```

### 6.3 With Timeouts

```python
# With timeouts and cancellation
async def execute_with_timeout(tasks: list, timeout: int = 600):
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=timeout
        )
        return results
    except asyncio.TimeoutError:
        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        raise TimeoutError(f"Execution exceeded {timeout}s")
```

---

## 7. Error Handling & Retry Logic

### 7.1 Exponential Backoff

```python
# Using tenacity library
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
)
async def call_api_with_retry(client, endpoint, data):
    response = await client.post(endpoint, json=data)
    response.raise_for_status()
    return response.json()
```

### 7.2 Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Circuit breaker for API calls"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failures = 0
        self.state = "closed"

    def on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "open"
```

---

## 8. Testing Strategy

### 8.1 TDD Workflow

**Phase 1: Write Tests**
```python
# tests/unit/test_orchestrator.py
import pytest
from ob1.orchestrator import Orchestrator
from ob1.agents.base import AgentType, AgentStatus

@pytest.mark.asyncio
async def test_orchestrator_creates_k_agents():
    """Test that orchestrator creates correct number of agents"""
    orchestrator = Orchestrator(
        repo_path="/tmp/test-repo",
        repo_url="https://github.com/test/repo",
    )

    # Mock agent execution
    with patch('ob1.orchestrator.AgentFactory.create') as mock_create:
        mock_agent = AsyncMock()
        mock_agent.execute_task.return_value = AgentResult(
            agent_id="test-1",
            agent_type=AgentType.CLAUDE,
            status=AgentStatus.COMPLETED,
        )
        mock_create.return_value = mock_agent

        results = await orchestrator.execute(
            task_description="Test task",
            num_agents=3,
        )

        assert len(results) == 3
        assert mock_create.call_count == 3
```

**Phase 2: Implement**
```python
# ob1/orchestrator.py
async def execute(self, task_description: str, num_agents: int = 3):
    # Implementation that makes tests pass
    ...
```

**Phase 3: Refactor**
```python
# Improve code quality while keeping tests passing
async def execute(self, task_description: str, num_agents: int = 3):
    # Refactored implementation with better structure
    ...
```

### 8.2 Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_claude_agent_full_workflow(tmp_path):
    """Integration test for Claude agent"""
    # Setup
    repo_path = tmp_path / "test-repo"
    setup_test_repo(repo_path)

    config = AgentConfig(
        agent_type=AgentType.CLAUDE,
        api_key=os.environ["ANTHROPIC_API_KEY"],
        workspace_path=str(repo_path),
        repo_url="https://github.com/test/repo",
    )

    agent = ClaudeAgent(config)

    # Execute
    async with agent:
        result = await agent.execute_task("Add hello world function")

    # Assert
    assert result.status == AgentStatus.COMPLETED
    assert result.pr_url is not None
    assert "pull" in result.pr_url
```

---

## 9. Deployment & CI/CD

### 9.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          pytest tests/unit -v --cov=ob1 --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 9.2 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml .
RUN pip install -e ".[prod]"

# Copy source
COPY ob1/ ./ob1/

# Run CLI
ENTRYPOINT ["ob1"]
```

---

## 10. Next Steps

### 10.1 MVP Checklist (Stage 1)

- [ ] Implement `BaseAgent` interface
- [ ] Implement `ClaudeAgent`
- [ ] Implement `OpenAIAgent`
- [ ] Implement `WorktreeManager`
- [ ] Implement `GitHubPRManager`
- [ ] Implement `Orchestrator`
- [ ] Implement `CLI`
- [ ] Write unit tests (80% coverage)
- [ ] Integration test with real APIs
- [ ] Create 3 PRs successfully

### 10.2 Stage 2: QA Testing Agent

- [ ] Design QA agent architecture
- [ ] Implement PR review logic
- [ ] Add build/test execution
- [ ] Add video recording (Playwright/Puppeteer)
- [ ] Integrate with GitHub Actions
- [ ] Create GitHub webhook listener

### 10.3 Future Enhancements

- [ ] Add more agents (Goose, Gemini, etc.)
- [ ] Implement voting/ranking system for PRs
- [ ] Add cost tracking and budgets
- [ ] Create web dashboard
- [ ] Add Slack/Discord notifications
- [ ] Implement PR merging logic

---

## Conclusion

This unified integration guide provides everything needed to implement the ob1 orchestrator with support for Claude, OpenAI, and Cursor agents. The architecture is:

- ✅ **Modular** - Easy to add new agents
- ✅ **Testable** - Following TDD principles
- ✅ **Async-first** - Maximum parallelism
- ✅ **Type-safe** - Complete type hints
- ✅ **Production-ready** - Error handling, logging, monitoring

**Time to MVP:** ~2-4 hours following TDD workflow

Good luck building! 🚀
