# Cursor Cloud Agent API & CLI - Comprehensive Research Documentation

**Research Date:** 2025-11-09
**Source:** https://cursor.com/docs/cloud-agent/api/overview
**Purpose:** Integration research for ob1 orchestrator to manage parallel AI coding agents

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [API Architecture](#api-architecture)
3. [Authentication](#authentication)
4. [Core Endpoints](#core-endpoints)
5. [Webhooks](#webhooks)
6. [CLI Tool](#cli-tool)
7. [Implementation Examples](#implementation-examples)
8. [Error Handling & Best Practices](#error-handling--best-practices)
9. [Integration with ob1 Orchestrator](#integration-with-ob1-orchestrator)
10. [Rate Limits & Quotas](#rate-limits--quotas)

---

## Executive Summary

Cursor provides two primary interfaces for AI-powered code automation:

1. **Cloud Agent API** - RESTful API for programmatic agent management
2. **Cursor CLI** - Command-line tool for both interactive and automated workflows

### Key Capabilities

- Launch AI agents on GitHub repositories
- Execute coding tasks asynchronously in isolated environments
- Create branches and pull requests automatically
- Support for follow-up instructions to active agents
- Webhook notifications for status changes
- Multiple model options (Claude 4 Sonnet, O3, Claude 4 Opus)

### Critical Limitations for ob1

- **No local worktree support** - Agents work directly on GitHub repositories, not local paths
- **GitHub-only** - Requires repositories to be on GitHub
- **No MCP support** - Model Context Protocol is currently unsupported
- **API-based only** - Cannot point CLI at custom local directories

**Impact on ob1:** Direct git worktree integration is not possible. Would require:
1. Push worktree to temporary GitHub branch
2. Launch Cursor agent on that branch
3. Pull results back to worktree

---

## API Architecture

### Base URL
```
https://api.cursor.com/v0
```

### Request/Response Format
- **Content-Type:** `application/json`
- **Authentication:** HTTP Basic Auth (API key as username, no password)
- **Response Format:** JSON

### Available Models
- `claude-4-sonnet-thinking` (default, recommended)
- `o3`
- `claude-4-opus-thinking`

**Recommendation:** Use "Auto" by not specifying a model - API will select optimal model

---

## Authentication

### Obtaining API Keys

1. Visit [Cursor Dashboard](https://cursor.com/settings)
2. Navigate to API Keys section
3. Generate new API key
4. Store securely in environment variables

### Using API Keys

**Environment Variable (Recommended):**
```bash
export CURSOR_API_KEY="your_api_key_here"
```

**HTTP Basic Auth Format:**
```
Username: YOUR_API_KEY
Password: (empty)
```

### Security Notes

- API keys are organization-scoped (visible to all admins)
- Keys remain valid even if creator's account status changes
- Store keys in environment variables, never commit to version control
- Use secrets management in CI/CD (GitHub Secrets, AWS Secrets Manager, etc.)

---

## Core Endpoints

### 1. Launch an Agent
**Endpoint:** `POST /v0/agents`

Creates a new cloud agent to work on a repository.

**Request Schema:**
```json
{
  "prompt": {
    "text": "string (required)",
    "images": [
      {
        "data": "base64_string",
        "width": 800,
        "height": 600
      }
    ]
  },
  "model": "claude-4-sonnet-thinking (optional)",
  "source": {
    "repository": "https://github.com/owner/repo (required)",
    "ref": "branch-name or commit-hash (optional)"
  },
  "target": {
    "branchName": "feature/custom-branch (optional)",
    "autoCreatePr": true,
    "openAsCursorGithubApp": false,
    "skipReviewerRequest": false
  },
  "webhook": {
    "url": "https://your-webhook-endpoint.com/notify",
    "secret": "minimum_32_character_secret_for_hmac"
  }
}
```

**Response:**
```json
{
  "id": "bc_abc123",
  "status": "CREATING",
  "source": {
    "repository": "https://github.com/owner/repo",
    "ref": "main"
  },
  "target": {
    "branchName": "cursor/agent-bc_abc123",
    "autoCreatePr": true
  },
  "createdAt": "2025-11-09T10:30:00Z"
}
```

**Status Flow:**
```
CREATING → RUNNING → FINISHED
         ↓
       ERROR
```

---

### 2. List Agents
**Endpoint:** `GET /v0/agents`

Retrieve all agents for authenticated user with pagination.

**Query Parameters:**
- `limit` (number): Results per page (default: 20, max: 100)
- `cursor` (string): Pagination cursor from previous response

**Response:**
```json
{
  "agents": [
    {
      "id": "bc_abc123",
      "name": "Agent working on feature X",
      "status": "RUNNING",
      "source": {
        "repository": "https://github.com/owner/repo",
        "ref": "main"
      },
      "target": {
        "url": "https://cursor.com/agents/bc_abc123",
        "branchName": "cursor/agent-bc_abc123",
        "pullRequestUrl": null
      },
      "summary": null,
      "createdAt": "2025-11-09T10:30:00Z"
    }
  ],
  "nextCursor": "eyJpZCI6ImJjX2FiYzEyMyJ9"
}
```

---

### 3. Get Agent Status
**Endpoint:** `GET /v0/agents/{id}`

Fetch current status and results for a specific agent.

**Path Parameters:**
- `id` (string): Agent identifier (e.g., "bc_abc123")

**Response:**
```json
{
  "id": "bc_abc123",
  "status": "FINISHED",
  "source": {
    "repository": "https://github.com/owner/repo",
    "ref": "main"
  },
  "target": {
    "url": "https://cursor.com/agents/bc_abc123",
    "branchName": "cursor/add-user-auth",
    "pullRequestUrl": "https://github.com/owner/repo/pull/42"
  },
  "summary": "Added user authentication with JWT tokens. Implemented login/logout endpoints and middleware.",
  "createdAt": "2025-11-09T10:30:00Z"
}
```

---

### 4. Get Agent Conversation
**Endpoint:** `GET /v0/agents/{id}/conversation`

Access full conversation history showing all prompts and responses.

**Path Parameters:**
- `id` (string): Agent identifier

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_001",
      "type": "user_message",
      "text": "Add user authentication with JWT tokens"
    },
    {
      "id": "msg_002",
      "type": "assistant_message",
      "text": "I'll add JWT-based authentication. Starting with dependencies..."
    },
    {
      "id": "msg_003",
      "type": "user_message",
      "text": "Also add rate limiting to the auth endpoints"
    },
    {
      "id": "msg_004",
      "type": "assistant_message",
      "text": "Added rate limiting middleware to auth routes..."
    }
  ]
}
```

**Important:** Cannot access conversation if agent has been deleted.

---

### 5. Add Follow-up
**Endpoint:** `POST /v0/agents/{id}/followup`

Send additional instructions to an active agent.

**Path Parameters:**
- `id` (string): Agent identifier

**Request Schema:**
```json
{
  "prompt": {
    "text": "Also add input validation to the login form",
    "images": []
  }
}
```

**Response:**
```json
{
  "id": "bc_abc123"
}
```

---

### 6. Delete Agent
**Endpoint:** `DELETE /v0/agents/{id}`

Permanently remove a cloud agent and its conversation history.

**Path Parameters:**
- `id` (string): Agent identifier

**Response:**
```json
{
  "id": "bc_abc123"
}
```

---

### 7. API Key Info
**Endpoint:** `GET /v0/me`

Verify authentication credentials.

**Response:**
```json
{
  "apiKeyName": "Production API Key",
  "createdAt": "2025-10-01T08:00:00Z",
  "userEmail": "dev@company.com"
}
```

---

### 8. List Models
**Endpoint:** `GET /v0/models`

Get available AI models.

**Response:**
```json
{
  "models": [
    "claude-4-sonnet-thinking",
    "o3",
    "claude-4-opus-thinking"
  ]
}
```

---

### 9. List Repositories
**Endpoint:** `GET /v0/repositories`

Access GitHub repositories available to authenticated user.

**Response:**
```json
{
  "repositories": [
    {
      "owner": "company",
      "name": "backend-api",
      "repository": "https://github.com/company/backend-api"
    },
    {
      "owner": "company",
      "name": "frontend-app",
      "repository": "https://github.com/company/frontend-app"
    }
  ]
}
```

**Rate Limits:** Strictly enforced
- 1 request per user per minute
- 30 requests per user per hour
- Response may take tens of seconds for users with many repositories

---

## Webhooks

### Overview
Webhooks provide real-time notifications about agent status changes via HTTP POST to your endpoint.

### Configuration
Set webhook during agent creation:

```json
{
  "webhook": {
    "url": "https://api.yourservice.com/cursor/webhooks",
    "secret": "at_least_32_characters_for_hmac_verification"
  }
}
```

### Supported Events
Currently only `statusChange` events when agent reaches:
- `ERROR` state
- `FINISHED` state

### Webhook Payload

```json
{
  "event": "statusChange",
  "timestamp": "2025-11-09T11:45:00Z",
  "id": "bc_abc123",
  "status": "FINISHED",
  "source": {
    "repository": "https://github.com/owner/repo",
    "ref": "main"
  },
  "target": {
    "url": "https://cursor.com/agents/bc_abc123",
    "branchName": "cursor/add-feature",
    "pullRequestUrl": "https://github.com/owner/repo/pull/42"
  },
  "summary": "Successfully implemented the requested feature"
}
```

### HMAC Signature Verification

**Header:** `X-Webhook-Signature`

**Format:** `sha256=<hex_digest>`

**Python Verification:**
```python
import hmac
import hashlib

def verify_webhook_signature(
    payload: bytes,
    signature_header: str,
    secret: str
) -> bool:
    """Verify webhook signature using HMAC-SHA256.

    Args:
        payload: Raw request body bytes (before JSON parsing)
        signature_header: Value of X-Webhook-Signature header
        secret: Webhook secret (minimum 32 characters)

    Returns:
        True if signature is valid, False otherwise
    """
    # Compute expected signature
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    expected_signature = f"sha256={expected}"

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature_header)

# Usage in Flask
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["CURSOR_WEBHOOK_SECRET"]

@app.route("/cursor/webhook", methods=["POST"])
def handle_cursor_webhook():
    # Get raw body BEFORE parsing JSON
    raw_body = request.get_data()
    signature = request.headers.get("X-Webhook-Signature")

    if not verify_webhook_signature(raw_body, signature, WEBHOOK_SECRET):
        abort(401, "Invalid signature")

    # Now safe to parse JSON
    payload = request.json

    if payload["event"] == "statusChange":
        agent_id = payload["id"]
        status = payload["status"]

        if status == "FINISHED":
            pr_url = payload["target"].get("pullRequestUrl")
            print(f"Agent {agent_id} finished: {pr_url}")
        elif status == "ERROR":
            print(f"Agent {agent_id} encountered error")

    return {"ok": True}, 200
```

**JavaScript Verification:**
```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signatureHeader, secret) {
  // Compute expected signature
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload, 'utf8');
  const expectedSignature = `sha256=${hmac.digest('hex')}`;

  // Constant-time comparison
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(signatureHeader)
  );
}

// Usage in Express
const express = require('express');
const app = express();

const WEBHOOK_SECRET = process.env.CURSOR_WEBHOOK_SECRET;

app.post('/cursor/webhook',
  express.raw({ type: 'application/json' }), // Get raw body
  (req, res) => {
    const signature = req.headers['x-webhook-signature'];

    if (!verifyWebhookSignature(req.body, signature, WEBHOOK_SECRET)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Parse JSON after verification
    const payload = JSON.parse(req.body);

    if (payload.event === 'statusChange') {
      const { id, status, target } = payload;

      if (status === 'FINISHED') {
        console.log(`Agent ${id} finished: ${target.pullRequestUrl}`);
      } else if (status === 'ERROR') {
        console.log(`Agent ${id} failed`);
      }
    }

    res.json({ ok: true });
  }
);
```

### Retry Logic
- Webhooks may be retried if endpoint returns error status code (4xx/5xx)
- Always return 2xx status code promptly to acknowledge receipt
- Process webhook asynchronously to avoid timeouts

### Best Practices
1. **Verify signatures** - Always validate HMAC before processing
2. **Use raw body** - Compute HMAC on raw bytes, not parsed JSON
3. **Return quickly** - Acknowledge with 2xx, then process async
4. **Use HTTPS** - Required in production for security
5. **Archive payloads** - Store raw webhooks for debugging and audit
6. **Handle retries** - Make webhook processing idempotent

---

## CLI Tool

### Overview
Cursor CLI (`cursor-agent`) enables command-line interaction with AI agents for both interactive and automated workflows.

### Installation

```bash
curl https://cursor.com/install -fsS | bash
```

This installs the `cursor-agent` command globally.

### Authentication

```bash
# Interactive login (opens browser)
cursor-agent login

# Non-interactive (CI/CD)
export CURSOR_API_KEY="your_api_key_here"

# Verify authentication
cursor-agent status
```

### Operating Modes

#### Interactive Mode

Start conversational session:
```bash
# Start with prompt
cursor-agent "Add user authentication"

# Start empty session
cursor-agent

# Resume previous session
cursor-agent resume

# Resume specific session
cursor-agent resume chat_abc123

# List previous sessions
cursor-agent ls
```

**Navigation:**
- **Arrow Up/Down** - Scroll through message history
- **Ctrl+R** - Review changes
  - `i` - Add follow-up instructions
  - Arrow keys - Navigate changes/files
- **Approve commands** - Press `y` or `n` before execution

**Context Management:**
- `@filename` - Include specific files
- `@folder/` - Include all files in folder
- `/compress` - Free up context window using summarization

#### Non-Interactive Mode (Headless)

For automation and scripting:

```bash
# Basic usage
cursor-agent --print "Analyze this codebase for security issues"

# With auto-apply changes
cursor-agent --print --force "Fix all linting errors"

# Specify model
cursor-agent --print --model claude-4-opus-thinking "Refactor auth module"

# JSON output for parsing
cursor-agent --print --output-format json "Find all TODOs"

# Streaming JSON for progress tracking
cursor-agent --print --output-format stream-json "Run tests and fix failures"
```

### CLI Parameters

| Flag | Description |
|------|-------------|
| `-a, --api-key <key>` | API key (or use CURSOR_API_KEY env var) |
| `-p, --print` | Non-interactive mode with output to stdout |
| `-f, --force` | Auto-apply changes without confirmation |
| `-m, --model <model>` | Specify AI model |
| `--output-format <fmt>` | Output format: text, json, stream-json |
| `--stream-partial-output` | Enable incremental streaming |
| `-b, --background` | Launch in background |
| `--fullscreen` | Full-screen interface |
| `--resume [chatId]` | Resume previous session |
| `-v, --version` | Show version |
| `-h, --help` | Show help |

### Configuration File

Create `.cursor/cli.json` to configure permissions:

```json
{
  "permissions": {
    "deny": [
      "Shell(git push)",
      "Shell(gh pr create)",
      "Write(**/secrets/**)",
      "Write(.env)"
    ],
    "allow": [
      "Shell(git status)",
      "Shell(git diff)",
      "Shell(pytest)",
      "Read(**)",
      "Write(**/src/**)",
      "Write(**/tests/**)"
    ]
  }
}
```

### Context Files

CLI automatically loads:
- `.cursor/rules` - Directory with rule files
- `AGENTS.md` - Root-level agent instructions
- `CLAUDE.md` - Root-level agent instructions
- `mcp.json` - Model Context Protocol servers

---

## Implementation Examples

### Python Implementation

#### Complete Async Client

```python
"""Cursor Cloud Agent API client with async support."""
import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import httpx


class AgentStatus(Enum):
    """Agent status values."""
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


@dataclass
class AgentSource:
    """Agent source configuration."""
    repository: str
    ref: Optional[str] = None


@dataclass
class AgentTarget:
    """Agent target configuration."""
    branch_name: Optional[str] = None
    auto_create_pr: bool = False
    open_as_cursor_github_app: bool = False
    skip_reviewer_request: bool = False


@dataclass
class Agent:
    """Agent response model."""
    id: str
    status: AgentStatus
    source: Dict[str, Any]
    target: Dict[str, Any]
    created_at: str
    summary: Optional[str] = None


class CursorClient:
    """Async client for Cursor Cloud Agent API."""

    BASE_URL = "https://api.cursor.com/v0"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize client.

        Args:
            api_key: Cursor API key. If None, reads from CURSOR_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("CURSOR_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set CURSOR_API_KEY or pass api_key.")

        # Create async client with basic auth
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            auth=(self.api_key, ""),  # Basic auth: username=api_key, password=""
            timeout=30.0,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def launch_agent(
        self,
        prompt: str,
        repository: str,
        ref: Optional[str] = None,
        branch_name: Optional[str] = None,
        auto_create_pr: bool = False,
        model: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> Agent:
        """Launch a new cloud agent.

        Args:
            prompt: Task instruction for the agent
            repository: GitHub repository URL
            ref: Branch, tag, or commit hash (default: main)
            branch_name: Custom branch name for agent work
            auto_create_pr: Auto-create PR when finished
            model: AI model to use (default: auto-select)
            webhook_url: Webhook endpoint for notifications
            webhook_secret: HMAC secret for webhook verification (min 32 chars)

        Returns:
            Agent object with id and initial status

        Raises:
            httpx.HTTPStatusError: On API error
        """
        payload: Dict[str, Any] = {
            "prompt": {"text": prompt},
            "source": {"repository": repository},
        }

        if ref:
            payload["source"]["ref"] = ref

        if branch_name or auto_create_pr:
            payload["target"] = {}
            if branch_name:
                payload["target"]["branchName"] = branch_name
            if auto_create_pr:
                payload["target"]["autoCreatePr"] = auto_create_pr

        if model:
            payload["model"] = model

        if webhook_url:
            payload["webhook"] = {"url": webhook_url}
            if webhook_secret:
                if len(webhook_secret) < 32:
                    raise ValueError("Webhook secret must be at least 32 characters")
                payload["webhook"]["secret"] = webhook_secret

        response = await self.client.post("/agents", json=payload)
        response.raise_for_status()

        data = response.json()
        return Agent(
            id=data["id"],
            status=AgentStatus(data["status"]),
            source=data["source"],
            target=data.get("target", {}),
            created_at=data["createdAt"],
            summary=data.get("summary"),
        )

    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent status.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent object with current status
        """
        response = await self.client.get(f"/agents/{agent_id}")
        response.raise_for_status()

        data = response.json()
        return Agent(
            id=data["id"],
            status=AgentStatus(data["status"]),
            source=data["source"],
            target=data.get("target", {}),
            created_at=data["createdAt"],
            summary=data.get("summary"),
        )

    async def list_agents(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> tuple[List[Agent], Optional[str]]:
        """List all agents with pagination.

        Args:
            limit: Results per page (max 100)
            cursor: Pagination cursor from previous response

        Returns:
            Tuple of (agents list, next_cursor)
        """
        params = {"limit": min(limit, 100)}
        if cursor:
            params["cursor"] = cursor

        response = await self.client.get("/agents", params=params)
        response.raise_for_status()

        data = response.json()
        agents = [
            Agent(
                id=a["id"],
                status=AgentStatus(a["status"]),
                source=a["source"],
                target=a.get("target", {}),
                created_at=a["createdAt"],
                summary=a.get("summary"),
            )
            for a in data.get("agents", [])
        ]

        return agents, data.get("nextCursor")

    async def add_followup(self, agent_id: str, prompt: str) -> Dict[str, str]:
        """Send follow-up instruction to active agent.

        Args:
            agent_id: Agent identifier
            prompt: Follow-up instruction

        Returns:
            Response with agent id
        """
        payload = {"prompt": {"text": prompt}}
        response = await self.client.post(f"/agents/{agent_id}/followup", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_conversation(self, agent_id: str) -> List[Dict[str, str]]:
        """Get agent conversation history.

        Args:
            agent_id: Agent identifier

        Returns:
            List of messages
        """
        response = await self.client.get(f"/agents/{agent_id}/conversation")
        response.raise_for_status()
        return response.json().get("messages", [])

    async def delete_agent(self, agent_id: str) -> Dict[str, str]:
        """Delete an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Response with agent id
        """
        response = await self.client.delete(f"/agents/{agent_id}")
        response.raise_for_status()
        return response.json()

    async def wait_for_completion(
        self,
        agent_id: str,
        poll_interval: float = 10.0,
        timeout: Optional[float] = None,
    ) -> Agent:
        """Poll agent until completion.

        Args:
            agent_id: Agent identifier
            poll_interval: Seconds between status checks
            timeout: Max seconds to wait (None = no limit)

        Returns:
            Final agent state

        Raises:
            asyncio.TimeoutError: If timeout exceeded
            RuntimeError: If agent reaches ERROR state
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            agent = await self.get_agent(agent_id)

            if agent.status == AgentStatus.FINISHED:
                return agent

            if agent.status == AgentStatus.ERROR:
                raise RuntimeError(f"Agent {agent_id} failed")

            if timeout:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    raise asyncio.TimeoutError(
                        f"Agent {agent_id} did not complete within {timeout}s"
                    )

            await asyncio.sleep(poll_interval)


# Example Usage
async def main():
    """Example usage of Cursor API client."""

    async with CursorClient() as client:
        # Launch agent
        agent = await client.launch_agent(
            prompt="Add user authentication with JWT tokens",
            repository="https://github.com/owner/repo",
            ref="main",
            auto_create_pr=True,
            webhook_url="https://api.myservice.com/cursor/webhook",
            webhook_secret="my_secure_webhook_secret_at_least_32_chars",
        )

        print(f"Launched agent: {agent.id}")
        print(f"Status: {agent.status.value}")

        # Add follow-up
        await asyncio.sleep(30)  # Wait a bit
        await client.add_followup(
            agent.id,
            "Also add rate limiting to the auth endpoints"
        )
        print("Added follow-up instruction")

        # Wait for completion (with timeout)
        try:
            final_agent = await client.wait_for_completion(
                agent.id,
                poll_interval=15.0,
                timeout=1800.0,  # 30 minutes
            )

            print(f"Agent completed!")
            print(f"Summary: {final_agent.summary}")
            print(f"PR: {final_agent.target.get('pullRequestUrl')}")

        except asyncio.TimeoutError:
            print(f"Agent did not complete within timeout")
        except RuntimeError as e:
            print(f"Agent failed: {e}")

        # Get conversation
        messages = await client.get_conversation(agent.id)
        print(f"\nConversation ({len(messages)} messages):")
        for msg in messages:
            print(f"  [{msg['type']}] {msg['text'][:100]}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### JavaScript/TypeScript Implementation

#### Complete Async Client

```typescript
/**
 * Cursor Cloud Agent API client with TypeScript support.
 */

enum AgentStatus {
  CREATING = "CREATING",
  RUNNING = "RUNNING",
  FINISHED = "FINISHED",
  ERROR = "ERROR",
}

interface AgentSource {
  repository: string;
  ref?: string;
}

interface AgentTarget {
  url?: string;
  branchName?: string;
  pullRequestUrl?: string;
}

interface Agent {
  id: string;
  status: AgentStatus;
  source: AgentSource;
  target: AgentTarget;
  createdAt: string;
  summary?: string;
}

interface LaunchAgentOptions {
  prompt: string;
  repository: string;
  ref?: string;
  branchName?: string;
  autoCreatePr?: boolean;
  model?: string;
  webhookUrl?: string;
  webhookSecret?: string;
}

interface ListAgentsResult {
  agents: Agent[];
  nextCursor?: string;
}

class CursorClient {
  private baseUrl = "https://api.cursor.com/v0";
  private apiKey: string;
  private authHeader: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.CURSOR_API_KEY || "";
    if (!this.apiKey) {
      throw new Error("API key required. Set CURSOR_API_KEY or pass apiKey.");
    }

    // Create basic auth header
    this.authHeader = `Basic ${Buffer.from(`${this.apiKey}:`).toString("base64")}`;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: this.authHeader,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API request failed: ${response.status} ${error}`);
    }

    return response.json();
  }

  async launchAgent(options: LaunchAgentOptions): Promise<Agent> {
    const {
      prompt,
      repository,
      ref,
      branchName,
      autoCreatePr = false,
      model,
      webhookUrl,
      webhookSecret,
    } = options;

    const payload: any = {
      prompt: { text: prompt },
      source: { repository },
    };

    if (ref) {
      payload.source.ref = ref;
    }

    if (branchName || autoCreatePr) {
      payload.target = {};
      if (branchName) {
        payload.target.branchName = branchName;
      }
      if (autoCreatePr) {
        payload.target.autoCreatePr = autoCreatePr;
      }
    }

    if (model) {
      payload.model = model;
    }

    if (webhookUrl) {
      payload.webhook = { url: webhookUrl };
      if (webhookSecret) {
        if (webhookSecret.length < 32) {
          throw new Error("Webhook secret must be at least 32 characters");
        }
        payload.webhook.secret = webhookSecret;
      }
    }

    return this.request<Agent>("/agents", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getAgent(agentId: string): Promise<Agent> {
    return this.request<Agent>(`/agents/${agentId}`);
  }

  async listAgents(
    limit: number = 20,
    cursor?: string
  ): Promise<ListAgentsResult> {
    const params = new URLSearchParams({
      limit: Math.min(limit, 100).toString(),
    });

    if (cursor) {
      params.append("cursor", cursor);
    }

    return this.request<ListAgentsResult>(`/agents?${params}`);
  }

  async addFollowup(agentId: string, prompt: string): Promise<{ id: string }> {
    return this.request(`/agents/${agentId}/followup`, {
      method: "POST",
      body: JSON.stringify({
        prompt: { text: prompt },
      }),
    });
  }

  async getConversation(agentId: string): Promise<Array<{
    id: string;
    type: string;
    text: string;
  }>> {
    const result = await this.request<{ messages: any[] }>(
      `/agents/${agentId}/conversation`
    );
    return result.messages;
  }

  async deleteAgent(agentId: string): Promise<{ id: string }> {
    return this.request(`/agents/${agentId}`, {
      method: "DELETE",
    });
  }

  async waitForCompletion(
    agentId: string,
    pollInterval: number = 10000,
    timeout?: number
  ): Promise<Agent> {
    const startTime = Date.now();

    while (true) {
      const agent = await this.getAgent(agentId);

      if (agent.status === AgentStatus.FINISHED) {
        return agent;
      }

      if (agent.status === AgentStatus.ERROR) {
        throw new Error(`Agent ${agentId} failed`);
      }

      if (timeout) {
        const elapsed = Date.now() - startTime;
        if (elapsed > timeout) {
          throw new Error(
            `Agent ${agentId} did not complete within ${timeout}ms`
          );
        }
      }

      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }
  }
}

// Example Usage
async function main() {
  const client = new CursorClient();

  try {
    // Launch agent
    const agent = await client.launchAgent({
      prompt: "Add user authentication with JWT tokens",
      repository: "https://github.com/owner/repo",
      ref: "main",
      autoCreatePr: true,
      webhookUrl: "https://api.myservice.com/cursor/webhook",
      webhookSecret: "my_secure_webhook_secret_at_least_32_chars",
    });

    console.log(`Launched agent: ${agent.id}`);
    console.log(`Status: ${agent.status}`);

    // Add follow-up
    await new Promise((resolve) => setTimeout(resolve, 30000));
    await client.addFollowup(
      agent.id,
      "Also add rate limiting to the auth endpoints"
    );
    console.log("Added follow-up instruction");

    // Wait for completion
    const finalAgent = await client.waitForCompletion(
      agent.id,
      15000, // 15s poll interval
      1800000 // 30 min timeout
    );

    console.log("Agent completed!");
    console.log(`Summary: ${finalAgent.summary}`);
    console.log(`PR: ${finalAgent.target.pullRequestUrl}`);

    // Get conversation
    const messages = await client.getConversation(agent.id);
    console.log(`\nConversation (${messages.length} messages):`);
    messages.forEach((msg) => {
      console.log(`  [${msg.type}] ${msg.text.substring(0, 100)}`);
    });

  } catch (error) {
    console.error("Error:", error);
  }
}

// Run example
main();
```

---

## Error Handling & Best Practices

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 401 | Unauthorized | Check API key |
| 404 | Not found | Verify agent ID/endpoint |
| 429 | Rate limited | Implement exponential backoff |
| 500 | Server error | Retry with backoff |
| 503 | Service unavailable | Retry later |

### Rate Limiting

**General Endpoints:**
- 20-100 requests/minute depending on endpoint
- Use 304 responses (ETags) where supported to avoid counting against limits

**Repository Listing:**
- 1 request per user per minute
- 30 requests per user per hour
- Strict enforcement

### Retry Strategy

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar("T")

async def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 16.0,
) -> T:
    """Retry function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except httpx.HTTPStatusError as e:
            last_exception = e

            # Don't retry client errors (except 429)
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                raise

            if attempt == max_retries:
                break

            # Exponential backoff
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)

    raise last_exception

# Usage
agent = await retry_with_backoff(
    lambda: client.launch_agent(prompt="...", repository="...")
)
```

### Best Practices

#### 1. Polling Efficiency

```python
# Good: Progressive backoff
async def smart_wait(client, agent_id):
    intervals = [5, 10, 15, 30, 60]  # Progressive intervals
    idx = 0

    while True:
        agent = await client.get_agent(agent_id)
        if agent.status in [AgentStatus.FINISHED, AgentStatus.ERROR]:
            return agent

        # Use progressively longer intervals
        interval = intervals[min(idx, len(intervals) - 1)]
        await asyncio.sleep(interval)
        idx += 1

# Bad: Constant rapid polling
async def bad_wait(client, agent_id):
    while True:
        agent = await client.get_agent(agent_id)
        if agent.status in [AgentStatus.FINISHED, AgentStatus.ERROR]:
            return agent
        await asyncio.sleep(1)  # Too frequent!
```

#### 2. Use Webhooks

```python
# Preferred: Event-driven with webhooks
agent = await client.launch_agent(
    prompt="...",
    repository="...",
    webhook_url="https://api.myservice.com/webhooks",
)
# Your webhook endpoint gets notified when done

# Fallback: Polling only if webhooks not available
agent = await client.wait_for_completion(agent.id)
```

#### 3. Proper Error Logging

```python
import logging

logger = logging.getLogger(__name__)

try:
    agent = await client.launch_agent(...)
except httpx.HTTPStatusError as e:
    logger.error(
        "Failed to launch agent",
        extra={
            "status_code": e.response.status_code,
            "response": e.response.text,
            "prompt": prompt[:100],
        }
    )
    raise
```

#### 4. Timeout Configuration

```python
# Configure appropriate timeouts
client = httpx.AsyncClient(
    base_url="https://api.cursor.com/v0",
    auth=(api_key, ""),
    timeout=httpx.Timeout(
        connect=10.0,    # Connection timeout
        read=30.0,       # Read timeout
        write=10.0,      # Write timeout
        pool=5.0,        # Pool timeout
    ),
)
```

#### 5. Resource Cleanup

```python
# Good: Always close clients
async with CursorClient() as client:
    agent = await client.launch_agent(...)
    # Client automatically closed

# Or explicit cleanup
client = CursorClient()
try:
    agent = await client.launch_agent(...)
finally:
    await client.close()
```

---

## Integration with ob1 Orchestrator

### Challenge: No Local Worktree Support

Cursor Cloud Agent API works exclusively with GitHub repositories, not local file paths. This presents a challenge for ob1's git worktree architecture.

### Proposed Integration Strategy

#### Option 1: Push-Based Workflow (Recommended)

```python
"""ob1 orchestrator integration with Cursor API."""
import asyncio
from pathlib import Path
from typing import List

from ob1.workspace.worktree import WorktreeManager
from ob1.agents.cursor import CursorClient


class CursorOrchestrator:
    """Orchestrate Cursor agents with git worktrees."""

    def __init__(
        self,
        repo_path: Path,
        github_repo: str,
        cursor_api_key: str,
    ):
        self.repo_path = repo_path
        self.github_repo = github_repo
        self.worktree_manager = WorktreeManager(repo_path)
        self.cursor_client = CursorClient(cursor_api_key)

    async def run_parallel_agents(
        self,
        task: str,
        num_agents: int = 3,
        base_branch: str = "main",
    ) -> List[str]:
        """Run multiple Cursor agents in parallel on same task.

        Strategy:
        1. Create temporary branches from base_branch
        2. Push branches to GitHub
        3. Launch Cursor agents on each branch
        4. Wait for completion
        5. Agents create PRs
        6. Return PR URLs for review

        Args:
            task: Task description for agents
            num_agents: Number of parallel agents
            base_branch: Base branch to work from

        Returns:
            List of PR URLs created by agents
        """
        # Step 1: Create and push temporary branches
        branches = []
        for i in range(num_agents):
            branch_name = f"cursor/agent-{i+1}/{task[:20]}"

            # Create branch locally
            await self._create_branch(branch_name, base_branch)

            # Push to GitHub
            await self._push_branch(branch_name)

            branches.append(branch_name)

        # Step 2: Launch agents in parallel
        agents = await asyncio.gather(*[
            self.cursor_client.launch_agent(
                prompt=task,
                repository=self.github_repo,
                ref=branch,
                auto_create_pr=True,
                branch_name=f"{branch}-work",
            )
            for branch in branches
        ])

        print(f"Launched {len(agents)} agents")

        # Step 3: Wait for all agents to complete
        results = await asyncio.gather(*[
            self.cursor_client.wait_for_completion(
                agent.id,
                poll_interval=15.0,
                timeout=1800.0,  # 30 min
            )
            for agent in agents
        ], return_exceptions=True)

        # Step 4: Extract PR URLs
        pr_urls = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Agent {i+1} failed: {result}")
                continue

            pr_url = result.target.get("pullRequestUrl")
            if pr_url:
                pr_urls.append(pr_url)
                print(f"Agent {i+1} created PR: {pr_url}")
            else:
                print(f"Agent {i+1} finished but no PR created")

        return pr_urls

    async def _create_branch(self, branch_name: str, base_branch: str):
        """Create new branch from base."""
        proc = await asyncio.create_subprocess_exec(
            "git", "branch", branch_name, base_branch,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _push_branch(self, branch_name: str):
        """Push branch to GitHub."""
        proc = await asyncio.create_subprocess_exec(
            "git", "push", "-u", "origin", branch_name,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()


# Example usage
async def main():
    orchestrator = CursorOrchestrator(
        repo_path=Path("/Users/sanchay/Documents/open-code-blocks"),
        github_repo="https://github.com/username/open-code-blocks",
        cursor_api_key="your_api_key",
    )

    pr_urls = await orchestrator.run_parallel_agents(
        task="Add user authentication with JWT tokens",
        num_agents=3,
        base_branch="main",
    )

    print(f"\nCreated {len(pr_urls)} PRs:")
    for url in pr_urls:
        print(f"  - {url}")
```

#### Option 2: CLI-Based Workflow (Alternative)

Use Cursor CLI in headless mode pointing at worktrees:

```python
"""Use Cursor CLI for local worktree integration."""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any


async def run_cursor_cli_in_worktree(
    worktree_path: Path,
    prompt: str,
    api_key: str,
) -> Dict[str, Any]:
    """Run Cursor CLI in non-interactive mode on worktree.

    Args:
        worktree_path: Path to git worktree
        prompt: Task instruction
        api_key: Cursor API key

    Returns:
        Parsed JSON result
    """
    proc = await asyncio.create_subprocess_exec(
        "cursor-agent",
        "--print",
        "--force",
        "--output-format", "json",
        prompt,
        cwd=worktree_path,
        env={"CURSOR_API_KEY": api_key},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Cursor CLI failed: {stderr.decode()}")

    return json.loads(stdout.decode())


# Usage in orchestrator
class CLIOrchestrator:
    """Orchestrate using CLI in worktrees."""

    async def run_parallel_agents(self, task: str, num_agents: int):
        """Run CLI agents in parallel worktrees."""
        # Create worktrees
        worktrees = [
            self.worktree_manager.create_worktree(f"agent-{i}")
            for i in range(num_agents)
        ]

        # Run CLI in each worktree
        results = await asyncio.gather(*[
            run_cursor_cli_in_worktree(wt, task, self.api_key)
            for wt in worktrees
        ])

        # Create PRs from worktrees
        pr_urls = []
        for i, result in enumerate(results):
            pr_url = await self._create_pr_from_worktree(worktrees[i], task)
            pr_urls.append(pr_url)

        return pr_urls
```

### Recommended Approach

**For ob1: Use Push-Based Workflow (Option 1)**

Reasons:
1. Cloud Agent API is more robust for parallel execution
2. Webhook support for event-driven architecture
3. Better error handling and monitoring
4. No CLI dependency in production

**Workflow:**
1. Create temporary branches in local repo
2. Push branches to GitHub
3. Launch Cloud Agents on branches
4. Agents work independently and create PRs
5. Review PRs and select best solution

---

## Rate Limits & Quotas

### API Rate Limits

| Endpoint | Limit | Scope |
|----------|-------|-------|
| List Repositories | 1/min, 30/hour | Per user |
| List Agents | Unknown | Per team |
| Launch Agent | Unknown | Per team |
| Get Agent Status | Unknown | Per team |
| Other endpoints | 20-100/min | Per team |

### Best Practices for Rate Limits

1. **Cache repository list** - List repositories once and cache
2. **Use webhooks** - Avoid polling for agent status
3. **Progressive backoff** - Increase polling intervals over time
4. **Batch operations** - Launch multiple agents together
5. **Monitor 429 responses** - Implement exponential backoff

### Pricing Considerations

Check [Cursor Pricing](https://cursor.com/docs/account/pricing#cloud-agent) for:
- Agent execution costs
- Model pricing differences
- Usage quotas
- Billing limits

---

## Appendix: Complete Working Example

### End-to-End Workflow

```python
"""Complete example: Launch agents, monitor via webhooks, review PRs."""
import asyncio
import os
from pathlib import Path
from flask import Flask, request, jsonify
import hmac
import hashlib

from cursor_client import CursorClient, AgentStatus


# ============================================================================
# Webhook Server
# ============================================================================

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["CURSOR_WEBHOOK_SECRET"]

# Store agent updates
agent_updates = {}

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook HMAC signature."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.route("/cursor/webhook", methods=["POST"])
def webhook():
    """Handle Cursor webhook notifications."""
    # Verify signature
    raw_body = request.get_data()
    signature = request.headers.get("X-Webhook-Signature")

    if not verify_signature(raw_body, signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Process webhook
    payload = request.json
    agent_id = payload["id"]
    status = payload["status"]

    agent_updates[agent_id] = payload

    print(f"Webhook: Agent {agent_id} → {status}")

    if status == "FINISHED":
        pr_url = payload["target"].get("pullRequestUrl")
        print(f"  PR: {pr_url}")

    return jsonify({"ok": True})


# ============================================================================
# Orchestrator
# ============================================================================

async def run_parallel_experiments(
    task: str,
    repository: str,
    num_agents: int = 3,
) -> list[str]:
    """Run parallel agents and return PR URLs."""

    async with CursorClient() as client:
        # Launch agents
        print(f"Launching {num_agents} agents...")
        agents = await asyncio.gather(*[
            client.launch_agent(
                prompt=task,
                repository=repository,
                auto_create_pr=True,
                webhook_url="https://api.myservice.com/cursor/webhook",
                webhook_secret=WEBHOOK_SECRET,
            )
            for _ in range(num_agents)
        ])

        print(f"Launched: {[a.id for a in agents]}")

        # Wait for all to complete
        results = await asyncio.gather(*[
            client.wait_for_completion(a.id, poll_interval=20.0, timeout=1800.0)
            for a in agents
        ], return_exceptions=True)

        # Extract PRs
        pr_urls = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Agent {i+1} failed: {result}")
                continue

            pr_url = result.target.get("pullRequestUrl")
            if pr_url:
                pr_urls.append(pr_url)

                # Get conversation for review
                messages = await client.get_conversation(result.id)
                print(f"\nAgent {i+1} conversation:")
                for msg in messages[-3:]:  # Last 3 messages
                    print(f"  [{msg['type']}] {msg['text'][:100]}")

        return pr_urls


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run complete workflow."""

    # Start webhook server in background thread
    from threading import Thread
    server_thread = Thread(
        target=lambda: app.run(host="0.0.0.0", port=8080),
        daemon=True
    )
    server_thread.start()

    # Run orchestration
    pr_urls = await run_parallel_experiments(
        task="Add user authentication with JWT tokens and rate limiting",
        repository="https://github.com/username/repo",
        num_agents=3,
    )

    print(f"\n{'='*60}")
    print(f"Completed! Created {len(pr_urls)} PRs:")
    for i, url in enumerate(pr_urls, 1):
        print(f"  {i}. {url}")
    print(f"{'='*60}")

    print("\nNext steps:")
    print("1. Review PRs and test each solution")
    print("2. Select best implementation")
    print("3. Merge winning PR")
    print("4. Close other PRs")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Summary

### What Works Well
- Launch multiple agents on same repository
- Automatic PR creation
- Webhook notifications for completion
- Follow-up instructions to running agents
- Multiple model options

### Current Limitations
- No local worktree/path support (GitHub only)
- No MCP protocol support
- Cannot directly point CLI at custom directories
- Rate limits on repository listing

### Recommended for ob1
1. **Use Cloud Agent API** (not CLI) for parallel orchestration
2. **Push-based workflow**: Create branches → Push → Launch agents → Review PRs
3. **Webhook-driven**: Use webhooks instead of polling
4. **Error handling**: Implement retry logic and proper error tracking
5. **Progressive polling**: If polling needed, increase intervals over time

### Key Integration Points

```python
# Core workflow for ob1
1. Create temporary branches from base
2. Push branches to GitHub
3. Launch Cursor agents via API
4. Receive webhook notifications
5. Review PRs and select winner
6. Clean up losing branches
```

This approach maintains ob1's parallel execution model while working within Cursor's GitHub-centric architecture.

---

**End of Documentation**
