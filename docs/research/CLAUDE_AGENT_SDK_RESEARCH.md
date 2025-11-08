# Claude Agent SDK - Comprehensive Documentation

**Research Date:** November 9, 2025
**SDK Version:** Latest (formerly Claude Code SDK)
**Official Documentation:** https://docs.claude.com/en/docs/agent-sdk/overview

---

## Table of Contents

1. [SDK Overview](#sdk-overview)
2. [Installation & Setup](#installation--setup)
3. [Authentication](#authentication)
4. [Agent Capabilities](#agent-capabilities)
5. [Integration Patterns](#integration-patterns)
6. [Code Examples](#code-examples)
7. [Best Practices](#best-practices)
8. [Error Handling & Rate Limiting](#error-handling--rate-limiting)
9. [Advanced Features](#advanced-features)

---

## SDK Overview

### What is Claude Agent SDK?

The Claude Agent SDK (formerly Claude Code SDK) is Anthropic's official framework for building production-ready AI agents. Built on the same infrastructure powering Claude Code, it provides all the building blocks needed to create autonomous agents that can:

- Understand and navigate codebases
- Read, write, and edit files
- Execute commands and scripts
- Perform web searches and fetch data
- Create commits and pull requests
- Manage complex multi-step workflows

### Available SDKs

| SDK | Language | Installation | GitHub Repository |
|-----|----------|--------------|-------------------|
| **TypeScript/JavaScript** | Node.js | `npm install @anthropic-ai/claude-agent-sdk` | [claude-agent-sdk-typescript](https://github.com/anthropics/claude-agent-sdk-typescript) |
| **Python** | Python 3.10+ | `pip install claude-agent-sdk` | [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) |

### Core Capabilities

- **Context Management**: Automatic context compaction and management to prevent overflow
- **Rich Tool Ecosystem**: File operations, code execution, web search, and extensibility via MCP
- **Fine-Grained Permissions**: Control agent capabilities through `allowedTools`, `disallowedTools`, and `permissionMode`
- **Production Features**: Built-in error handling, session management, and monitoring
- **Performance Optimization**: Automatic prompt caching and Claude API integration

### Architecture Pattern

The SDK follows a feedback loop architecture:

1. **Gather Context** - Retrieve relevant information from available sources
2. **Take Action** - Execute tasks using available tools
3. **Verify Work** - Evaluate and improve outputs
4. **Repeat** - Iterate until objectives are met

---

## Installation & Setup

### TypeScript/JavaScript

#### Prerequisites
- Node.js (latest LTS recommended)
- Claude API key from [Anthropic Console](https://console.anthropic.com/)

#### Installation
```bash
npm install @anthropic-ai/claude-agent-sdk
```

#### Basic Setup
```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const result = query({
  prompt: "Your task here",
  options: {
    model: "claude-sonnet-4-5",
    cwd: process.cwd(),
    allowedTools: ['Read', 'Write', 'Bash']
  }
});

for await (const message of result) {
  console.log(message);
}
```

### Python

#### Prerequisites
- Python 3.10 or higher
- Node.js (required for some features)
- Claude Code 2.0.0+ (optional, for CLI features)

#### Installation
```bash
pip install claude-agent-sdk

# Optional: Install Claude Code CLI
npm install -g @anthropic-ai/claude-code
```

#### Basic Setup
```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

asyncio.run(main())
```

---

## Authentication

### Environment Variables

The SDK supports multiple authentication methods with the following precedence:

1. **Anthropic API Key** (Primary Method)
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

2. **Amazon Bedrock**
   ```bash
   export CLAUDE_CODE_USE_BEDROCK=1
   # Also set AWS credentials
   export AWS_ACCESS_KEY_ID="your-key"
   export AWS_SECRET_ACCESS_KEY="your-secret"
   export AWS_REGION="us-east-1"
   ```

3. **Google Vertex AI**
   ```bash
   export CLAUDE_CODE_USE_VERTEX=1
   # Also configure Google Cloud credentials
   ```

### Configuration Files

The SDK also loads API keys from:
- Project settings: `.claude/settings.json`
- User settings: `~/.claude/settings.json`
- Organization credentials
- Temporary tokens

#### TypeScript Configuration
```typescript
const result = query({
  prompt: "task",
  options: {
    apiKeySource: 'project' // or 'user', 'organization'
  }
});
```

---

## Agent Capabilities

### Creating Agent Sessions

#### Python: Simple Query (Stateless)

Each `query()` call starts fresh with no memory of previous interactions.

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/user/project",
        allowed_tools=["Read", "Write", "Bash"]
    )

    async for message in query(
        prompt="Create a Python web server",
        options=options
    ):
        print(message)

asyncio.run(main())
```

#### Python: Session Client (Stateful)

`ClaudeSDKClient` maintains conversation context across multiple exchanges.

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful coding assistant",
        allowed_tools=["Read", "Grep", "Write"]
    )

    async with ClaudeSDKClient(options=options) as client:
        # First query
        await client.query("Find all Python files in the project")
        async for msg in client.receive_response():
            print(msg)

        # Follow-up query (maintains context)
        await client.query("Now analyze the main.py file")
        async for msg in client.receive_response():
            print(msg)

asyncio.run(main())
```

#### TypeScript: Basic Query

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const result = query({
  prompt: "List all TypeScript files",
  options: {
    model: "claude-sonnet-4-5",
    cwd: "/path/to/project",
    allowedTools: ['Glob', 'Read'],
    maxTurns: 10
  }
});

for await (const msg of result) {
  if (msg.type === 'result') {
    console.log("Complete:", msg.result);
  }
}
```

### System Prompts

System prompts define your agent's role, expertise, and behavior.

#### Python Example
```python
options = ClaudeAgentOptions(
    system_prompt="""You are a senior Python developer specializing in:
    - Writing clean, maintainable code
    - Following PEP 8 style guidelines
    - Implementing comprehensive tests
    - Using type hints everywhere

    Always explain your reasoning before making changes.""",
    max_turns=20
)
```

#### TypeScript Example
```typescript
const result = query({
  prompt: "Refactor this code",
  options: {
    systemPrompt: {
      type: 'text',
      text: 'You are an expert in TypeScript and functional programming.'
    }
  }
});
```

### Sending Messages and Tasks

#### Python: Processing Different Message Types

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are a code reviewer",
        max_turns=1
    )

    async for message in query(
        prompt="Review main.py for security issues",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Response: {block.text}")
                elif block.type == "tool_use":
                    print(f"Using tool: {block.tool_name}")

asyncio.run(main())
```

#### TypeScript: Handling Streaming Messages

```typescript
for await (const msg of query({
    prompt: "Explain the authentication flow",
    options: {
        maxTurns: 5,
        allowedTools: ["Read", "Grep"],
        includePartialMessages: true  // Enable real-time streaming
    }
})) {
    switch (msg.type) {
        case 'assistant':
            console.log("Assistant:", msg.content);
            break;
        case 'result':
            console.log("Final result:", msg.result);
            break;
        case 'partial':
            console.log("Streaming:", msg.delta);
            break;
    }
}
```

### Built-in Tools

The SDK provides a comprehensive set of built-in tools:

#### File Operations
- **Read** - Load file contents with optional offset/limit
- **Write** - Create or overwrite files
- **Edit** - Replace text in files (precise string replacement)
- **Glob** - Pattern-based file matching (e.g., `**/*.py`)
- **Grep** - Regex search with context options

#### Code Execution
- **Bash** - Execute shell commands with timeout support
- **NotebookEdit** - Jupyter notebook cell operations

#### Web Operations
- **WebFetch** - Fetch and analyze URLs
- **WebSearch** - Web search with domain filtering

#### Advanced
- **Task** - Delegate to specialized subagents
- **TodoWrite** - Manage task lists
- **ListMcpResources** - Enumerate MCP resources
- **ReadMcpResource** - Access MCP resource content

#### Example: Restricting Tools

```python
# Python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],  # Only allow these tools
    disallowed_tools=["Bash", "Write"]       # Explicitly block these
)
```

```typescript
// TypeScript
const result = query({
  prompt: "Analyze the codebase",
  options: {
    allowedTools: ['Read', 'Grep', 'Glob'],
    disallowedTools: ['Bash', 'Write']
  }
});
```

### Working with Files and Repositories

#### Python: Repository Analysis

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def analyze_repository():
    options = ClaudeAgentOptions(
        cwd="/path/to/repo",
        allowed_tools=["Read", "Grep", "Glob", "Bash"],
        system_prompt="""Analyze this repository:
        1. Find all Python files
        2. Identify the main entry point
        3. List all dependencies
        4. Check for tests"""
    )

    async for msg in query(
        prompt="Analyze this repository structure",
        options=options
    ):
        print(msg)

asyncio.run(analyze_repository())
```

#### TypeScript: Multi-Directory Access

```typescript
const result = query({
  prompt: "Find all configuration files",
  options: {
    cwd: "/path/to/main-project",
    additionalDirectories: [
      "/path/to/shared-libs",
      "/path/to/config"
    ],
    allowedTools: ['Glob', 'Read']
  }
});
```

### Git Operations and Creating PRs

Git operations are performed through the Bash tool or specialized workflows.

#### Python: Git Commit Example

```python
async def create_commit():
    options = ClaudeAgentOptions(
        cwd="/path/to/repo",
        allowed_tools=["Bash", "Read", "Write"],
        permission_mode="acceptEdits"
    )

    async for msg in query(
        prompt="""
        1. Review the changes with git diff
        2. Create a commit with a descriptive message
        3. Follow conventional commit format
        """,
        options=options
    ):
        print(msg)
```

#### TypeScript: PR Workflow

```typescript
const result = query({
  prompt: `
    1. Create a new branch called 'feature/new-api'
    2. Make the necessary code changes
    3. Commit the changes with proper message
    4. Push to origin
    5. Create a PR using gh CLI
  `,
  options: {
    allowedTools: ['Read', 'Write', 'Edit', 'Bash'],
    permissionMode: 'acceptEdits'
  }
});
```

#### Best Practices for Git Operations

According to Anthropic engineers, Claude handles 90%+ of git interactions effectively:

- **Commit messages**: Claude analyzes diffs and recent history to compose contextual messages
- **PR creation**: Use shorthand like "pr" - Claude understands the context
- **Complex operations**: Reverting files, resolving rebase conflicts, comparing patches

---

## Integration Patterns

### Async/Await Patterns

Both SDKs use native async iteration for streaming responses.

#### Python: Basic Async Pattern

```python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="Hello, Claude!"):
        # Process each message as it arrives
        print(message)

asyncio.run(main())
```

#### Python: Using anyio (Alternative)

```python
import anyio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

#### Python: Concurrent Operations

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def task1():
    async for msg in query("Analyze file1.py"):
        print("Task 1:", msg)

async def task2():
    async for msg in query("Analyze file2.py"):
        print("Task 2:", msg)

async def main():
    # Run multiple queries concurrently
    await asyncio.gather(task1(), task2())

asyncio.run(main())
```

#### TypeScript: Async Iteration

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

async function main() {
  for await (const msg of query({ prompt: "task" })) {
    if (msg.type === 'result') {
      console.log("Complete:", msg.result);
    }
  }
}

main();
```

#### TypeScript: Manual Streaming with Interrupts

```typescript
const q = query({ prompt: "Long-running task" });

// Start processing
setTimeout(() => {
  q.interrupt();  // Stop mid-execution
}, 5000);

for await (const msg of q) {
  console.log(msg);
}
```

### Streaming vs Non-Streaming Responses

#### Streaming Mode (Recommended)

**When to use:**
- Rich, interactive experiences requiring real-time feedback
- Multi-turn conversations with natural context persistence
- Applications needing dynamic message queueing
- Systems requiring lifecycle hooks and real-time interruption

**Python Example:**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def streaming_example():
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant",
        max_turns=10
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Explain async programming")

        # Stream responses in real-time
        async for response in client.receive_response():
            print(f"Streaming: {response}")

asyncio.run(streaming_example())
```

**TypeScript Example:**
```typescript
const result = query({
  prompt: "Explain the codebase",
  options: {
    includePartialMessages: true  // Enable partial message events
  }
});

for await (const msg of result) {
  if (msg.type === 'partial') {
    // Real-time feedback as Claude is thinking
    process.stdout.write(msg.delta);
  }
}
```

#### Single Message Mode

**When to use:**
- One-shot responses
- Stateless environments (AWS Lambda)
- Simple queries without complex interactions
- Simplicity over interactivity

**Python Example:**
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def single_shot():
    options = ClaudeAgentOptions(max_turns=1)

    async for msg in query(
        prompt="What is the capital of France?",
        options=options
    ):
        print(msg)

asyncio.run(single_shot())
```

**TypeScript Example:**
```typescript
// Simple one-shot query
const result = query({
  prompt: "Calculate 2 + 2",
  options: { maxTurns: 1 }
});

const messages = [];
for await (const msg of result) {
  messages.push(msg);
}

console.log(messages[messages.length - 1]);
```

### Error Handling

#### Python: Comprehensive Error Handling

```python
from claude_agent_sdk import (
    query,
    ClaudeSDKError,
    CLINotFoundError,
    CLIConnectionError,
    ProcessError,
    CLIJSONDecodeError
)

async def safe_query():
    try:
        async for message in query(prompt="Hello"):
            print(message)

    except CLINotFoundError:
        print("ERROR: Claude Code CLI not installed")
        print("Install with: npm install -g @anthropic-ai/claude-code")

    except CLIConnectionError as e:
        print(f"ERROR: Connection failed: {e}")
        print("Check your network connection and API key")

    except ProcessError as e:
        print(f"ERROR: Process failed with exit code {e.exit_code}")
        print(f"stderr: {e.stderr}")

    except CLIJSONDecodeError as e:
        print(f"ERROR: Failed to parse response: {e}")

    except ClaudeSDKError as e:
        print(f"ERROR: SDK error: {e}")

asyncio.run(safe_query())
```

#### TypeScript: Error Handling

```typescript
import { query, AbortError } from '@anthropic-ai/claude-agent-sdk';

async function safeQuery() {
  try {
    for await (const msg of query({ prompt: "task" })) {
      if (msg.type === 'result') {
        if (msg.subtype === 'error_during_execution') {
          console.error("Execution failed:", msg.error);
        } else if (msg.subtype === 'error_max_turns') {
          console.error("Max turns exceeded");
        }
      }
    }
  } catch (error) {
    if (error instanceof AbortError) {
      console.log("Operation interrupted by user");
    } else {
      console.error("Unexpected error:", error);
    }
  }
}
```

### Rate Limiting

The Claude API has rate limits for:
- **RPM**: Requests per minute
- **ITPM**: Input tokens per minute
- **OTPM**: Output tokens per minute

#### Python: Rate Limit Handling with Exponential Backoff

```python
from anthropic import RateLimitError, APIError
import time
import random

async def query_with_retry(prompt: str, max_retries: int = 5):
    """Query with exponential backoff on rate limits."""

    for attempt in range(max_retries):
        try:
            async for msg in query(prompt=prompt):
                return msg

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Final attempt failed

            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limited. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
            await asyncio.sleep(wait_time)

        except APIError as e:
            print(f"API error: {e}")
            raise

# Usage
asyncio.run(query_with_retry("Analyze the codebase"))
```

#### Monitoring Usage

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def track_usage():
    async for msg in query("Complete task"):
        if hasattr(msg, 'type') and msg.type == 'result':
            if hasattr(msg, 'usage'):
                print(f"Input tokens: {msg.usage.input_tokens}")
                print(f"Output tokens: {msg.usage.output_tokens}")
                print(f"Cost: ${msg.total_cost_usd:.4f}")
```

---

## Code Examples

### Complete Python Workflow Examples

#### Example 1: File Analysis Agent

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def analyze_python_files():
    """Analyze all Python files in a project for code quality."""

    options = ClaudeAgentOptions(
        cwd="/path/to/project",
        allowed_tools=["Glob", "Read", "Grep"],
        system_prompt="""You are a Python code quality expert.
        Analyze files for:
        - PEP 8 compliance
        - Security vulnerabilities
        - Performance issues
        - Missing documentation
        """,
        max_turns=15
    )

    async for message in query(
        prompt="""
        1. Find all Python files in the project
        2. Analyze each file for code quality
        3. Provide a summary of findings
        4. Suggest improvements
        """,
        options=options
    ):
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    print(block.text)

asyncio.run(analyze_python_files())
```

#### Example 2: Custom Tools with MCP

```python
import asyncio
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions
)

# Define custom tools
@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    """Add two numbers together."""
    result = args['a'] + args['b']
    return {
        "content": [{
            "type": "text",
            "text": f"The sum of {args['a']} and {args['b']} is {result}"
        }]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    """Multiply two numbers."""
    result = args['a'] * args['b']
    return {
        "content": [{
            "type": "text",
            "text": f"The product of {args['a']} and {args['b']} is {result}"
        }]
    }

@tool("calculate", "Evaluate a mathematical expression", {"expression": str})
async def calculate(args):
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow safe mathematical operations
        allowed_names = {
            "abs": abs, "max": max, "min": min,
            "sum": sum, "pow": pow, "round": round
        }
        result = eval(args["expression"], {"__builtins__": {}}, allowed_names)
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error evaluating expression: {str(e)}"
            }],
            "is_error": True
        }

async def main():
    # Create MCP server with tools
    calculator = create_sdk_mcp_server(
        name="calculator",
        version="2.0.0",
        tools=[add, multiply, calculate]
    )

    # Configure agent options
    options = ClaudeAgentOptions(
        mcp_servers={"calc": calculator},
        allowed_tools=[
            "mcp__calc__add",
            "mcp__calc__multiply",
            "mcp__calc__calculate"
        ],
        system_prompt="You are a mathematical assistant. Use the calculator tools to help users with math."
    )

    # Use the agent
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What is 15 multiplied by 7, then add 23?")

        async for msg in client.receive_response():
            if hasattr(msg, 'content'):
                for block in msg.content:
                    if hasattr(block, 'text'):
                        print(block.text)

asyncio.run(main())
```

#### Example 3: Repository Integration with Git

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def create_feature_branch():
    """Create a feature branch, make changes, and create a PR."""

    options = ClaudeAgentOptions(
        cwd="/path/to/repo",
        allowed_tools=["Bash", "Read", "Write", "Edit", "Grep"],
        permission_mode="acceptEdits",
        system_prompt="""You are a senior developer following git best practices.
        Always:
        - Write clear, descriptive commit messages
        - Follow conventional commit format
        - Test changes before committing
        - Create atomic commits
        """
    )

    async for msg in query(
        prompt="""
        1. Check git status to see current branch
        2. Create a new branch called 'feature/add-logging'
        3. Add logging to all Python files in src/
        4. Run tests to ensure nothing broke
        5. Create a commit with message: 'feat: add comprehensive logging to src modules'
        6. Push the branch to origin
        7. Create a PR using gh CLI with title 'Add comprehensive logging' and body explaining changes
        """,
        options=options
    ):
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    print(block.text)

asyncio.run(create_feature_branch())
```

#### Example 4: Multi-Turn Conversation

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interactive_debugging():
    """Interactive debugging session with context preservation."""

    options = ClaudeAgentOptions(
        cwd="/path/to/project",
        allowed_tools=["Read", "Grep", "Bash"],
        system_prompt="You are a debugging expert. Help identify and fix issues systematically."
    )

    async with ClaudeSDKClient(options=options) as client:
        # First query
        print("=== Finding error logs ===")
        await client.query("Find all error logs in the application")
        async for msg in client.receive_response():
            print(msg)

        # Follow-up query (maintains context from first query)
        print("\n=== Analyzing most recent error ===")
        await client.query("Analyze the most recent error and suggest a fix")
        async for msg in client.receive_response():
            print(msg)

        # Third query (still maintains full context)
        print("\n=== Implementing fix ===")
        await client.query("Implement the suggested fix")
        async for msg in client.receive_response():
            print(msg)

asyncio.run(interactive_debugging())
```

### Complete TypeScript Workflow Examples

#### Example 1: Codebase Analysis

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

async function analyzeCodebase() {
  const result = query({
    prompt: `
      Analyze this TypeScript codebase:
      1. Find all .ts and .tsx files
      2. Identify architectural patterns
      3. Check for potential issues
      4. Suggest improvements
    `,
    options: {
      model: 'claude-sonnet-4-5',
      cwd: '/path/to/project',
      allowedTools: ['Glob', 'Read', 'Grep'],
      systemPrompt: 'You are a TypeScript expert specializing in code architecture.',
      maxTurns: 20
    }
  });

  for await (const msg of result) {
    if (msg.type === 'assistant') {
      console.log('Analysis:', msg.content);
    } else if (msg.type === 'result') {
      console.log('Complete. Usage:', msg.usage);
    }
  }
}

analyzeCodebase();
```

#### Example 2: MCP Server Integration

```typescript
import { query, createSdkMcpServer, tool } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

// Define custom tools with Zod schemas
const weatherTool = tool(
  'GetWeather',
  'Fetch current weather for a city',
  z.object({
    city: z.string().describe('City name'),
    units: z.enum(['celsius', 'fahrenheit']).default('celsius')
  }),
  async (args) => {
    // In a real app, this would call a weather API
    return {
      content: [{
        type: 'text',
        text: `The weather in ${args.city} is sunny and 72°${args.units === 'celsius' ? 'C' : 'F'}`
      }]
    };
  }
);

const newsTool = tool(
  'GetNews',
  'Fetch latest news headlines',
  z.object({
    category: z.enum(['tech', 'business', 'sports']).default('tech')
  }),
  async (args) => {
    return {
      content: [{
        type: 'text',
        text: `Top ${args.category} news: [Latest headlines would go here]`
      }]
    };
  }
);

async function main() {
  // Create MCP server with tools
  const server = createSdkMcpServer({
    name: 'info-tools',
    tools: [weatherTool, newsTool]
  });

  // Use the agent
  const result = query({
    prompt: 'What is the weather in San Francisco and the latest tech news?',
    options: {
      mcpServers: {
        'info': { type: 'sdk', name: 'info-tools', instance: server }
      },
      allowedTools: ['mcp__info__GetWeather', 'mcp__info__GetNews']
    }
  });

  for await (const msg of result) {
    console.log(msg);
  }
}

main();
```

---

## Best Practices

### 1. Prompt Engineering for Code Generation

#### Be Specific and Contextual

**Good:**
```python
options = ClaudeAgentOptions(
    system_prompt="""You are a Python backend developer.
    Tech stack: FastAPI, PostgreSQL, SQLAlchemy, Pytest

    Follow these standards:
    - Use type hints everywhere
    - Write docstrings in Google format
    - Create unit tests for all new functions
    - Follow PEP 8 style guide
    - Use async/await for I/O operations
    """,
    cwd="/path/to/project"
)

prompt = """
Create a new API endpoint for user registration:
- POST /api/v1/users/register
- Accept: email, password, username
- Validate email format and password strength
- Hash password with bcrypt
- Return JWT token on success
- Include comprehensive error handling
- Write unit tests with 90%+ coverage
"""
```

**Bad:**
```python
prompt = "Create a user registration endpoint"
```

#### Use Multi-Step Instructions

```python
prompt = """
Step 1: Analyze the existing authentication system
Step 2: Identify where to add the new feature
Step 3: Implement the feature following existing patterns
Step 4: Add comprehensive tests
Step 5: Update documentation
Step 6: Create a commit with conventional commit message
"""
```

### 2. Context Management

#### Use CLAUDE.md for Project Memory

Create `.claude/CLAUDE.md` or `CLAUDE.md` in your project root:

```markdown
# Project: MyApp

## Tech Stack
- Frontend: React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, PostgreSQL
- Testing: Pytest, Jest, React Testing Library

## Architecture
- Follows clean architecture pattern
- API routes in `src/api/routes/`
- Business logic in `src/services/`
- Data models in `src/models/`

## Code Standards
- All Python code must have type hints
- 90% test coverage required
- Use conventional commits
- No TODO comments without GitHub issues

## Never Do
- Never use `any` type in TypeScript
- Never commit directly to main branch
- Never skip tests
```

Then load it:

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],  # Load .claude/CLAUDE.md
    cwd="/path/to/project"
)
```

```typescript
const result = query({
  prompt: "Add new feature",
  options: {
    settingSources: ['project'],  // Load .claude/CLAUDE.md
    cwd: '/path/to/project'
  }
});
```

### 3. Error Recovery and Verification

#### Implement Verification Loops

```python
prompt = """
1. Implement the feature
2. Run the tests
3. If tests fail:
   a. Analyze the failure
   b. Fix the issue
   c. Go back to step 2
4. Only proceed when all tests pass
"""
```

### 4. Resource Management

#### Set Appropriate Limits

```python
options = ClaudeAgentOptions(
    max_turns=20,  # Prevent infinite loops
    model="claude-sonnet-4-5",  # Choose appropriate model
)
```

#### Clean Up Sessions

```python
# Use context managers for automatic cleanup
async with ClaudeSDKClient(options=options) as client:
    await client.query("Task")
    # Automatic disconnect on exit
```

---

## Error Handling & Rate Limiting

### Error Types and Handling

#### Python Error Hierarchy

```python
from claude_agent_sdk import (
    ClaudeSDKError,        # Base exception
    CLINotFoundError,      # Claude Code CLI not installed
    CLIConnectionError,    # Connection issues
    ProcessError,          # Process execution failures
    CLIJSONDecodeError    # JSON parsing failures
)
```

### Rate Limiting Strategies

#### Understanding Rate Limits

Claude API enforces these limits:
- **RPM (Requests Per Minute)**: Maximum API calls per minute
- **ITPM (Input Tokens Per Minute)**: Maximum input tokens per minute
- **OTPM (Output Tokens Per Minute)**: Maximum output tokens per minute

When exceeded, you'll receive a **429** error with a `retry-after` header.

#### Exponential Backoff Implementation

```python
import asyncio
import random
from anthropic import RateLimitError, APIError
from claude_agent_sdk import query, ClaudeAgentOptions

async def query_with_backoff(
    prompt: str,
    options: ClaudeAgentOptions = None,
    max_retries: int = 5,
    base_delay: float = 1.0
):
    """Execute query with exponential backoff on rate limits."""

    for attempt in range(max_retries):
        try:
            messages = []
            async for msg in query(prompt=prompt, options=options):
                messages.append(msg)
            return messages

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Final attempt failed

            # Exponential backoff with jitter
            delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)

            print(f"Rate limited. Retry {attempt + 1}/{max_retries} after {delay:.2f}s")
            await asyncio.sleep(delay)

        except APIError as e:
            print(f"API error: {e}")

            # Some errors are retryable
            if e.status_code in (500, 502, 503, 504):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Server error. Retrying after {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue

            raise  # Non-retryable error

# Usage
asyncio.run(query_with_backoff("Complete task", max_retries=5))
```

---

## Advanced Features

### 1. Subagents for Parallel Execution

Subagents enable specialized agents with isolated contexts working on specific tasks.

#### Python: Defining Subagents

Create subagent definitions in `.claude/agents/`:

**`.claude/agents/code-reviewer.md`:**
```markdown
# Code Reviewer

You are an expert code reviewer specializing in:
- Security vulnerabilities
- Performance issues
- Code smells
- Best practices

## Process
1. Read the files to review
2. Analyze for issues
3. Provide specific, actionable feedback
4. Rate severity: HIGH, MEDIUM, LOW

## Output Format
Provide a structured review with:
- File path
- Line numbers
- Issue description
- Suggested fix
- Severity
```

### 2. MCP (Model Context Protocol) Integration

MCP enables integration with external services and data sources.

#### Complete MCP Example

```python
import asyncio
import httpx
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions
)

# Database tool
@tool("query_db", "Query the database", {"sql": str})
async def query_database(args):
    """Execute a SQL query (with safety checks)."""

    sql = args['sql'].lower()

    # Safety: Only allow SELECT
    if not sql.strip().startswith('select'):
        return {
            "content": [{
                "type": "text",
                "text": "Error: Only SELECT queries allowed"
            }],
            "is_error": True
        }

    # In a real app, execute the query
    # For demo, return mock data
    return {
        "content": [{
            "type": "text",
            "text": "Query results: [...]"
        }]
    }

# API tool
@tool("fetch_api", "Fetch data from external API", {"endpoint": str})
async def fetch_from_api(args):
    """Fetch data from an external API."""

    endpoint = args['endpoint']

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/{endpoint}")
            response.raise_for_status()
            data = response.json()

        return {
            "content": [{
                "type": "text",
                "text": f"API Response: {data}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"API Error: {str(e)}"
            }],
            "is_error": True
        }

# Create MCP server
integration_server = create_sdk_mcp_server(
    name="integrations",
    version="1.0.0",
    tools=[query_database, fetch_from_api]
)

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={"integrations": integration_server},
        allowed_tools=[
            "mcp__integrations__query_db",
            "mcp__integrations__fetch_api",
            "Read",
            "Write"
        ],
        system_prompt="You can query the database and fetch from APIs to complete tasks."
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Fetch user data from the API and save to a file")

        async for msg in client.receive_response():
            print(msg)

asyncio.run(main())
```

---

## Comparison: Python vs TypeScript SDK

| Feature | Python | TypeScript |
|---------|--------|------------|
| **Installation** | `pip install claude-agent-sdk` | `npm install @anthropic-ai/claude-agent-sdk` |
| **Prerequisites** | Python 3.10+, Node.js | Node.js |
| **Primary Function** | `query()` | `query()` |
| **Session Client** | `ClaudeSDKClient` | Built into `query()` |
| **Custom Tools** | `@tool` decorator | `tool()` function |
| **MCP Creation** | `create_sdk_mcp_server()` | `createSdkMcpServer()` |
| **Type Safety** | Type hints with mypy | Native TypeScript |
| **Async Pattern** | `async/await` with asyncio/anyio | `async/await` native |
| **Error Types** | Specific exception classes | Error subtypes in messages |
| **Streaming** | `async for` iteration | `for await` iteration |

### When to Use Python

- Building data science/ML workflows
- Integrating with Python-heavy stacks (Django, FastAPI, etc.)
- Existing Python tooling and infrastructure
- Jupyter notebook workflows
- Scientific computing applications

### When to Use TypeScript

- Building web applications
- Node.js backends
- Integrating with JavaScript/TypeScript projects
- Frontend agent interfaces
- Serverless functions (AWS Lambda, Vercel, etc.)

---

## Resources and Links

### Official Documentation

- **Agent SDK Overview**: https://docs.claude.com/en/docs/agent-sdk/overview
- **Python API Reference**: https://docs.claude.com/en/api/agent-sdk/python
- **TypeScript API Reference**: https://docs.claude.com/en/api/agent-sdk/typescript
- **Streaming vs Single Mode**: https://docs.claude.com/en/api/agent-sdk/streaming-vs-single-mode
- **Migration Guide**: https://docs.claude.com/en/docs/claude-code/sdk/migration-guide

### GitHub Repositories

- **Python SDK**: https://github.com/anthropics/claude-agent-sdk-python
- **TypeScript SDK**: https://github.com/anthropics/claude-agent-sdk-typescript
- **Claude Code**: https://github.com/anthropics/claude-code
- **Skills Repository**: https://github.com/anthropics/skills

### Tutorials and Guides

- **Building Agents**: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- **Claude Code Best Practices**: https://www.anthropic.com/engineering/claude-code-best-practices
- **DataCamp Tutorial**: https://www.datacamp.com/tutorial/how-to-use-claude-agent-sdk

---

## Conclusion

The Claude Agent SDK provides a powerful framework for building production-ready AI agents in both Python and TypeScript. Key takeaways:

1. **Start Simple**: Begin with basic `query()` calls and gradually add complexity
2. **Use System Prompts**: Define clear roles and expectations for your agents
3. **Manage Context**: Use CLAUDE.md, subagents, and compaction strategically
4. **Handle Errors**: Implement comprehensive error handling and rate limiting
5. **Test Thoroughly**: Create test cases for agent behavior
6. **Monitor Usage**: Track costs and token usage
7. **Leverage Tools**: Use built-in tools and create custom ones for specialized needs
8. **Apply Best Practices**: Follow the engineering principles for reliable agents

The SDK's feedback loop architecture (gather → act → verify → repeat) combined with its rich tooling ecosystem makes it suitable for everything from simple automation tasks to complex multi-agent systems handling production workflows.

---

**Document Version:** 1.0
**Last Updated:** November 9, 2025
**Research conducted for:** ob1 - Parallel AI SWE Orchestrator project
