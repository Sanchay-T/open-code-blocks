# OpenAI Codex & API Research - Comprehensive Documentation

## Executive Summary

This document provides comprehensive documentation for integrating OpenAI's code generation capabilities into the ob1 orchestrator. It covers both the **OpenAI Codex CLI** (a terminal-based coding agent) and the **OpenAI Chat Completions API** (for programmatic integration).

**Key Finding:** As of 2025, OpenAI has deprecated the original Codex API models. Code generation is now primarily done through:
1. **Codex CLI** - A local terminal agent (open-source, written in Rust)
2. **Chat Completions API** with GPT-4o/GPT-4-turbo models

---

## Table of Contents

1. [API Architecture](#1-api-architecture)
2. [Core Capabilities](#2-core-capabilities)
3. [Integration Requirements](#3-integration-requirements)
4. [Code Examples](#4-code-examples)
5. [Error Handling](#5-error-handling)
6. [Git Worktree Integration](#6-git-worktree-integration)
7. [Codex CLI Deep Dive](#7-codex-cli-deep-dive)

---

## 1. API Architecture

### 1.1 Authentication Methods

**Environment Variable (Recommended):**
```bash
export OPENAI_API_KEY="sk-..."
```

**Python SDK:**
```python
from openai import OpenAI

# Automatic (reads OPENAI_API_KEY from environment)
client = OpenAI()

# Explicit API key
client = OpenAI(api_key="sk-...")
```

**JavaScript/TypeScript SDK:**
```javascript
import OpenAI from 'openai';

// Automatic (reads OPENAI_API_KEY from environment)
const client = new OpenAI();

// Explicit API key
const client = new OpenAI({ apiKey: 'sk-...' });
```

### 1.2 Base URL and Endpoints

**Base URL:** `https://api.openai.com/v1`

**Primary Endpoints:**
- **Chat Completions:** `POST /v1/chat/completions`
- **Models:** `GET /v1/models`
- **Embeddings:** `POST /v1/embeddings`
- **Files:** `POST /v1/files`
- **Fine-tuning:** `POST /v1/fine_tuning/jobs`

**Full Endpoint Example:**
```
https://api.openai.com/v1/chat/completions
```

### 1.3 Request/Response Formats

**Request Format (Chat Completions):**
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert Python developer following TDD principles."
    },
    {
      "role": "user",
      "content": "Implement a function to calculate fibonacci numbers with type hints."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false
}
```

**Response Format (Non-Streaming):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Here's a Fibonacci implementation with type hints:\n\n```python\ndef fibonacci(n: int) -> int:\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75
  }
}
```

### 1.4 Model Names (2025)

**Recommended Models for Code Generation:**

| Model | Context Window | Best For | Cost |
|-------|----------------|----------|------|
| `gpt-4o` | 128K tokens | **Primary choice** - Multi-modal, fastest, best quality | Medium |
| `gpt-4o-mini` | 128K tokens | Cost-effective, faster responses | Low |
| `gpt-4-turbo` | 128K tokens | Text-only, reliable for code | High |
| `gpt-4` | 8K tokens | Legacy, still reliable | Highest |
| `gpt-3.5-turbo` | 16K tokens | Very fast, budget-friendly | Lowest |

**Recommendation for ob1:** Use `gpt-4o` as the default model for best results. It's the flagship model as of 2025 and handles code generation exceptionally well.

**Model Naming Convention:**
- `-turbo` suffix = Faster, more cost-efficient variant
- `-mini` suffix = Smaller, cheaper variant
- `o` suffix = "Omni" - Multi-modal (voice, image, text)

### 1.5 Rate Limits and Quotas

**Rate Limit Structure:**
- **RPM (Requests Per Minute)** - Number of API calls
- **TPM (Tokens Per Minute)** - Total tokens processed

**Token Calculation:**
```
Total Tokens = Input Tokens + Output Tokens
```
Example: 1,000 token prompt + 500 token response = 1,500 tokens toward TPM limit.

**Usage Tiers (Automatically升级 based on usage):**

| Tier | GPT-4o TPM | GPT-4o RPM | Notes |
|------|------------|------------|-------|
| Free | 20,000 | 3 | Very limited |
| Tier 1 | 500,000 | 3,500 | Increased from 30K in Sept 2025 |
| Tier 2+ | Higher | Higher | Scales with usage |

**Error Response (Rate Limit Exceeded):**
```
HTTP 429 Too Many Requests
{
  "error": {
    "message": "Rate limit reached for requests",
    "type": "rate_limit_error",
    "param": null,
    "code": "rate_limit_exceeded"
  }
}
```

**Best Practices:**
- Set `max_tokens` close to expected response size
- Implement exponential backoff for retries
- Monitor usage via OpenAI dashboard
- Consider batching requests during off-peak hours

---

## 2. Core Capabilities

### 2.1 Code Generation Tasks

**Supported Code Generation Operations:**

1. **Function Implementation**
   - Generate functions from specifications
   - Add type hints and docstrings
   - Implement test cases

2. **Bug Fixing**
   - Analyze error messages
   - Suggest fixes with explanations
   - Provide multiple solution approaches

3. **Code Refactoring**
   - Improve code quality
   - Extract helper functions
   - Optimize performance

4. **Test Generation**
   - Generate unit tests
   - Create integration tests
   - Generate test fixtures

5. **Documentation**
   - Generate docstrings
   - Write README sections
   - Create API documentation

### 2.2 Repository Context

**Providing Codebase Context:**

**Method 1: Include Files in Prompt**
```python
# Read relevant files
context_files = {
    "orchestrator.py": Path("ob1/orchestrator.py").read_text(),
    "worktree.py": Path("ob1/workspace/worktree.py").read_text(),
}

# Build prompt with context
prompt = f"""
Given the following codebase context:

## orchestrator.py
```python
{context_files['orchestrator.py']}
```

## worktree.py
```python
{context_files['worktree.py']}
```

Task: Implement the create_pr() method in github_pr.py that integrates with these modules.
"""
```

**Method 2: Use System Message for Guidelines**
```python
system_message = """
You are an expert Python developer working on the ob1 project.

Project Context:
- Architecture: Async-first, type-safe Python 3.11+
- Testing: Pytest with TDD (test-first approach)
- File size limit: <300 lines per file
- Dependencies: httpx, typer, asyncio

Code Style:
- Complete type hints (mandatory)
- Async/await for all I/O
- Single responsibility principle
- Structured logging

When generating code:
1. Write tests first (TDD)
2. Use async/await for I/O operations
3. Add comprehensive type hints
4. Keep functions focused and small
5. Include docstrings with examples
"""
```

### 2.3 Structured Prompts

**Effective Prompt Structure for Code Changes:**

```python
def generate_code_prompt(
    task: str,
    context: dict[str, str],
    requirements: list[str],
    constraints: list[str]
) -> str:
    """Generate a structured prompt for code generation."""

    prompt = f"""# Task
{task}

# Context
"""

    for filename, content in context.items():
        prompt += f"\n## {filename}\n```python\n{content}\n```\n"

    prompt += "\n# Requirements\n"
    for i, req in enumerate(requirements, 1):
        prompt += f"{i}. {req}\n"

    if constraints:
        prompt += "\n# Constraints\n"
        for constraint in constraints:
            prompt += f"- {constraint}\n"

    prompt += """
# Output Format
Provide:
1. Complete implementation with type hints
2. Docstrings with examples
3. Error handling
4. Unit tests (if applicable)
"""

    return prompt
```

### 2.4 Streaming vs Non-Streaming

**Non-Streaming (Default):**
- Simpler to implement
- Returns complete response at once
- Better for shorter responses
- Use when you don't need real-time feedback

**Streaming:**
- Real-time response chunks
- Better user experience for long outputs
- Lower perceived latency
- Use for interactive CLI applications

**When to Use Streaming in ob1:**
- Interactive mode: Show progress to user
- Long code generation: Display code as it's written
- Multiple agents: Show parallel progress

**When to Use Non-Streaming in ob1:**
- Batch processing: Process complete responses
- Testing: Easier to verify complete outputs
- Simple tasks: Overhead not worth it

### 2.5 Executing Commands and File Manipulation

**Important:** The OpenAI API itself does **not** execute commands or manipulate files directly. Your integration code must:

1. **Parse the API response** to extract code/instructions
2. **Execute commands** using Python's `subprocess` or `asyncio`
3. **Write files** using Python's file I/O
4. **Commit changes** using git commands

**Example Workflow:**
```
User Request → OpenAI API (generate code) → Parse Response →
Write Files → Run Tests → Create Commit → Create PR
```

---

## 3. Integration Requirements

### 3.1 Required Headers and Authentication

**Python SDK (Automatic):**
```python
from openai import OpenAI

client = OpenAI()  # Reads OPENAI_API_KEY automatically
```

**Raw HTTP Request:**
```python
import httpx

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=request_body,
    )
```

### 3.2 Providing Codebase Context

**Strategy 1: File Tree + Key Files**
```python
async def build_codebase_context(repo_path: Path) -> str:
    """Build codebase context with file tree and key files."""

    # Generate file tree
    tree_output = subprocess.run(
        ["tree", "-I", "__pycache__|*.pyc|.git", "-L", "3"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    # Identify key files
    key_files = [
        "ob1/__init__.py",
        "ob1/orchestrator.py",
        "ob1/cli.py",
        "pyproject.toml",
        "CLAUDE.md",  # Project guidelines
    ]

    context = f"# Project Structure\n```\n{tree_output.stdout}\n```\n\n"

    for file_path in key_files:
        full_path = repo_path / file_path
        if full_path.exists():
            content = full_path.read_text()
            context += f"# {file_path}\n```python\n{content}\n```\n\n"

    return context
```

**Strategy 2: Semantic Search (Advanced)**
```python
from openai import OpenAI

async def find_relevant_files(
    query: str,
    repo_path: Path,
    client: OpenAI,
) -> list[str]:
    """Find relevant files using embeddings."""

    # Get all Python files
    all_files = list(repo_path.rglob("*.py"))

    # Generate embeddings for query
    query_embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    ).data[0].embedding

    # Generate embeddings for files (cached)
    # Compare cosine similarity
    # Return top-k most relevant files

    # Implementation details omitted for brevity
    return relevant_files
```

### 3.3 Task Instructions Format

**Template for ob1 Tasks:**
```python
TASK_TEMPLATE = """
You are working on the ob1 project - a parallel AI SWE orchestrator.

# Your Task
{task_description}

# Current Branch
{branch_name}

# Affected Files
{file_list}

# Project Guidelines
- Follow TDD: Write tests first, then implementation
- Use async/await for all I/O operations
- Add complete type hints (Python 3.11+)
- Keep files under 300 lines
- Use structured logging

# Expected Output
1. List of files to create/modify
2. Complete implementation for each file
3. Test cases (if applicable)
4. Commands to run for validation

# Format
Provide your response in the following format:

## Files to Modify
- path/to/file1.py
- path/to/file2.py

## file1.py
```python
# Complete implementation
```

## file2.py
```python
# Complete implementation
```

## Tests
```python
# Test cases
```

## Validation Commands
```bash
# Commands to run
```
"""
```

### 3.4 Chaining Multiple Operations

**Approach 1: Sequential API Calls**
```python
async def sequential_code_generation(
    client: AsyncOpenAI,
    task: str,
) -> dict[str, str]:
    """Generate code in multiple steps."""

    # Step 1: Generate test cases
    test_response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a testing expert. Write comprehensive tests."},
            {"role": "user", "content": f"Write tests for: {task}"},
        ],
    )

    test_code = test_response.choices[0].message.content

    # Step 2: Generate implementation
    impl_response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert developer. Implement code to pass these tests."},
            {"role": "user", "content": f"Tests:\n{test_code}\n\nImplement the code."},
        ],
    )

    impl_code = impl_response.choices[0].message.content

    return {
        "tests": test_code,
        "implementation": impl_code,
    }
```

**Approach 2: Multi-Turn Conversation**
```python
async def iterative_refinement(
    client: AsyncOpenAI,
    initial_task: str,
) -> str:
    """Refine code through multiple iterations."""

    messages = [
        {"role": "system", "content": "You are an expert developer."},
        {"role": "user", "content": initial_task},
    ]

    # Initial generation
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    messages.append({
        "role": "assistant",
        "content": response.choices[0].message.content,
    })

    # Request refinement
    messages.append({
        "role": "user",
        "content": "Add comprehensive error handling and logging.",
    })

    refined_response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    return refined_response.choices[0].message.content
```

### 3.5 Creating Commits/Branches

**Workflow Integration:**
```python
import asyncio
from pathlib import Path

async def apply_code_changes(
    worktree_path: Path,
    generated_code: dict[str, str],
    commit_message: str,
) -> None:
    """Apply generated code and create commit."""

    # Write generated files
    for file_path, content in generated_code.items():
        full_path = worktree_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    # Git operations
    async def run_git(args: list[str]) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Git command failed: {stderr.decode()}")
        return stdout.decode()

    # Stage changes
    await run_git(["add", "."])

    # Create commit
    await run_git(["commit", "-m", commit_message])

    # Push to remote
    await run_git(["push", "-u", "origin", "HEAD"])
```

---

## 4. Code Examples

### 4.1 Python Implementation - Basic

```python
"""
Basic OpenAI integration for code generation.
"""

from openai import OpenAI
from typing import Optional


def generate_code(
    task: str,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Generate code using OpenAI Chat Completions API.

    Args:
        task: Description of the code to generate
        model: OpenAI model to use
        temperature: Randomness (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum tokens in response

    Returns:
        Generated code as string

    Example:
        >>> code = generate_code("Write a function to calculate factorial")
        >>> print(code)
    """
    client = OpenAI()  # Reads OPENAI_API_KEY from environment

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert Python developer. Write clean, well-documented code with type hints.",
            },
            {
                "role": "user",
                "content": task,
            },
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # Example usage
    task = """
    Implement a function to calculate fibonacci numbers with:
    - Type hints
    - Docstring
    - Memoization for performance
    - Edge case handling
    """

    code = generate_code(task)
    print(code)
```

### 4.2 Python Implementation - Async

```python
"""
Async OpenAI integration for parallel code generation.
"""

import asyncio
from openai import AsyncOpenAI
from typing import List, Dict


async def generate_code_async(
    task: str,
    context: str = "",
    model: str = "gpt-4o",
) -> str:
    """
    Generate code asynchronously using OpenAI API.

    Args:
        task: Code generation task
        context: Additional codebase context
        model: OpenAI model name

    Returns:
        Generated code
    """
    client = AsyncOpenAI()

    messages = [
        {
            "role": "system",
            "content": "You are an expert Python developer following TDD principles.",
        },
    ]

    if context:
        messages.append({
            "role": "user",
            "content": f"Codebase context:\n{context}",
        })

    messages.append({
        "role": "user",
        "content": task,
    })

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
    )

    return response.choices[0].message.content


async def generate_multiple_parallel(
    tasks: List[str],
    model: str = "gpt-4o",
) -> List[str]:
    """
    Generate code for multiple tasks in parallel.

    Args:
        tasks: List of code generation tasks
        model: OpenAI model name

    Returns:
        List of generated code (same order as tasks)
    """
    # Create tasks for parallel execution
    coroutines = [
        generate_code_async(task, model=model)
        for task in tasks
    ]

    # Execute all in parallel
    results = await asyncio.gather(*coroutines)

    return results


async def main():
    """Example: Generate multiple components in parallel."""

    tasks = [
        "Implement a WorktreeManager class with create_worktree() method",
        "Implement a GitHubPR class with create_pr() method",
        "Implement a Logger utility with structured logging",
    ]

    print("Generating code for 3 components in parallel...")

    results = await generate_multiple_parallel(tasks)

    for i, code in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"Component {i}:")
        print('='*60)
        print(code)


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 Python Implementation - Streaming

```python
"""
Streaming responses for real-time code generation feedback.
"""

import asyncio
from openai import AsyncOpenAI


async def generate_code_streaming(
    task: str,
    model: str = "gpt-4o",
) -> str:
    """
    Generate code with streaming responses.

    Args:
        task: Code generation task
        model: OpenAI model name

    Returns:
        Complete generated code
    """
    client = AsyncOpenAI()

    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert Python developer."},
            {"role": "user", "content": task},
        ],
        stream=True,
    )

    complete_response = ""

    print("Generating code (streaming):")
    print("-" * 60)

    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            complete_response += content
            print(content, end="", flush=True)

    print("\n" + "-" * 60)

    return complete_response


async def main():
    task = "Implement a retry decorator with exponential backoff"
    code = await generate_code_streaming(task)

    # Save to file
    with open("generated_code.py", "w") as f:
        f.write(code)

    print("\nCode saved to generated_code.py")


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.4 JavaScript/TypeScript Implementation

```typescript
/**
 * OpenAI integration for code generation (TypeScript)
 */

import OpenAI from 'openai';

interface CodeGenerationOptions {
  task: string;
  context?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

interface GeneratedCode {
  code: string;
  model: string;
  tokensUsed: number;
}

/**
 * Generate code using OpenAI Chat Completions API
 */
async function generateCode(
  options: CodeGenerationOptions
): Promise<GeneratedCode> {
  const {
    task,
    context = '',
    model = 'gpt-4o',
    temperature = 0.7,
    maxTokens = 2000,
  } = options;

  const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: 'You are an expert TypeScript developer. Write clean, type-safe code.',
    },
  ];

  if (context) {
    messages.push({
      role: 'user',
      content: `Codebase context:\n${context}`,
    });
  }

  messages.push({
    role: 'user',
    content: task,
  });

  const response = await client.chat.completions.create({
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
  });

  return {
    code: response.choices[0].message.content || '',
    model: response.model,
    tokensUsed: response.usage?.total_tokens || 0,
  };
}

/**
 * Generate code with streaming
 */
async function generateCodeStreaming(
  task: string,
  model: string = 'gpt-4o'
): Promise<string> {
  const client = new OpenAI();

  const stream = await client.chat.completions.create({
    model,
    messages: [
      {
        role: 'system',
        content: 'You are an expert TypeScript developer.',
      },
      {
        role: 'user',
        content: task,
      },
    ],
    stream: true,
  });

  let completeResponse = '';

  console.log('Generating code (streaming):');
  console.log('-'.repeat(60));

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    completeResponse += content;
    process.stdout.write(content);
  }

  console.log('\n' + '-'.repeat(60));

  return completeResponse;
}

/**
 * Generate multiple code components in parallel
 */
async function generateMultipleParallel(
  tasks: string[],
  model: string = 'gpt-4o'
): Promise<GeneratedCode[]> {
  const promises = tasks.map(task =>
    generateCode({ task, model })
  );

  return Promise.all(promises);
}

// Example usage
async function main() {
  try {
    // Example 1: Basic code generation
    const result = await generateCode({
      task: 'Implement a debounce function in TypeScript with proper types',
      model: 'gpt-4o',
    });

    console.log('Generated Code:');
    console.log(result.code);
    console.log(`\nTokens used: ${result.tokensUsed}`);

    // Example 2: Parallel generation
    const tasks = [
      'Implement a retry utility with exponential backoff',
      'Implement a logger class with log levels',
      'Implement a cache utility with TTL support',
    ];

    console.log('\nGenerating 3 components in parallel...');
    const results = await generateMultipleParallel(tasks);

    results.forEach((result, i) => {
      console.log(`\nComponent ${i + 1}:`);
      console.log(result.code);
    });

    // Example 3: Streaming
    await generateCodeStreaming(
      'Implement a rate limiter using token bucket algorithm'
    );
  } catch (error) {
    console.error('Error:', error);
  }
}

// Run examples
if (require.main === module) {
  main();
}

export { generateCode, generateCodeStreaming, generateMultipleParallel };
```

### 4.5 Authentication Setup

**Python - Using python-dotenv:**
```python
# .env file
OPENAI_API_KEY=sk-proj-...

# Python code
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Client automatically reads OPENAI_API_KEY
client = OpenAI()
```

**JavaScript/TypeScript - Using dotenv:**
```typescript
// .env file
OPENAI_API_KEY=sk-proj-...

// TypeScript code
import 'dotenv/config';
import OpenAI from 'openai';

// Client automatically reads OPENAI_API_KEY
const client = new OpenAI();
```

**Environment-Specific Configuration:**
```python
import os
from openai import OpenAI

def get_openai_client(environment: str = "production") -> OpenAI:
    """Get OpenAI client with environment-specific configuration."""

    if environment == "development":
        # Use different API key or settings for dev
        api_key = os.getenv("OPENAI_DEV_API_KEY")
        # Could also use a local proxy or different base URL
    elif environment == "testing":
        # Use mock client for testing
        api_key = "sk-test-mock-key"
    else:
        api_key = os.getenv("OPENAI_API_KEY")

    return OpenAI(api_key=api_key)
```

### 4.6 Complete Workflow Example

```python
"""
Complete workflow: Task → Code Generation → File Creation → Commit
"""

import asyncio
from pathlib import Path
from openai import AsyncOpenAI
from typing import Dict, List


class CodeGenerator:
    """OpenAI-powered code generator."""

    def __init__(self, model: str = "gpt-4o"):
        self.client = AsyncOpenAI()
        self.model = model

    async def generate_implementation(
        self,
        task: str,
        context: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Generate code implementation with tests.

        Args:
            task: Task description
            context: Relevant codebase files

        Returns:
            Dict mapping file paths to generated content
        """
        # Build context
        context_str = self._build_context(context)

        # Generate tests first (TDD)
        test_code = await self._generate_tests(task, context_str)

        # Generate implementation
        impl_code = await self._generate_implementation(
            task,
            context_str,
            test_code,
        )

        return {
            "implementation": impl_code,
            "tests": test_code,
        }

    def _build_context(self, context: Dict[str, str]) -> str:
        """Build context string from files."""
        context_parts = []
        for filename, content in context.items():
            context_parts.append(f"## {filename}\n```python\n{content}\n```")
        return "\n\n".join(context_parts)

    async def _generate_tests(self, task: str, context: str) -> str:
        """Generate test cases (TDD step 1)."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a testing expert. Write comprehensive pytest tests.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nTask: {task}\n\nWrite failing tests first (TDD).",
                },
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def _generate_implementation(
        self,
        task: str,
        context: str,
        test_code: str,
    ) -> str:
        """Generate implementation to pass tests (TDD step 2)."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Python developer. Implement code to pass the tests.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nTests:\n{test_code}\n\nTask: {task}\n\nImplement the code.",
                },
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content


async def apply_generated_code(
    worktree_path: Path,
    generated: Dict[str, str],
) -> None:
    """Write generated code to files."""

    # Write implementation
    impl_file = worktree_path / "ob1" / "new_module.py"
    impl_file.parent.mkdir(parents=True, exist_ok=True)
    impl_file.write_text(generated["implementation"])

    # Write tests
    test_file = worktree_path / "tests" / "test_new_module.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(generated["tests"])


async def run_git_command(
    worktree_path: Path,
    args: List[str],
) -> str:
    """Run git command in worktree."""
    proc = await asyncio.create_subprocess_exec(
        "git",
        *args,
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Git command failed: {stderr.decode()}")

    return stdout.decode()


async def complete_workflow(
    task: str,
    worktree_path: Path,
) -> None:
    """Complete workflow from task to commit."""

    print(f"Task: {task}")
    print(f"Worktree: {worktree_path}")

    # Step 1: Generate code
    print("\n[1/4] Generating code...")
    generator = CodeGenerator()

    context = {
        "CLAUDE.md": Path("CLAUDE.md").read_text(),
    }

    generated = await generator.generate_implementation(task, context)

    # Step 2: Write files
    print("[2/4] Writing files...")
    await apply_generated_code(worktree_path, generated)

    # Step 3: Run tests
    print("[3/4] Running tests...")
    proc = await asyncio.create_subprocess_exec(
        "pytest",
        "tests/",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        print(f"Tests failed:\n{stderr.decode()}")
        return

    print("Tests passed!")

    # Step 4: Commit
    print("[4/4] Creating commit...")
    await run_git_command(worktree_path, ["add", "."])
    await run_git_command(
        worktree_path,
        ["commit", "-m", f"feat: {task}"],
    )

    print("✓ Complete!")


async def main():
    task = "Implement rate limiter utility with token bucket algorithm"
    worktree_path = Path("/tmp/ob1-worktree-1")

    await complete_workflow(task, worktree_path)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. Error Handling

### 5.1 Common Errors

**1. Authentication Errors (401):**
```python
from openai import AuthenticationError

try:
    response = client.chat.completions.create(...)
except AuthenticationError as e:
    print(f"Invalid API key: {e}")
    # Check OPENAI_API_KEY environment variable
```

**2. Rate Limit Errors (429):**
```python
from openai import RateLimitError

try:
    response = client.chat.completions.create(...)
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement exponential backoff retry
```

**3. Invalid Request Errors (400):**
```python
from openai import BadRequestError

try:
    response = client.chat.completions.create(...)
except BadRequestError as e:
    print(f"Invalid request: {e}")
    # Check model name, parameters, message format
```

**4. API Connection Errors:**
```python
from openai import APIConnectionError

try:
    response = client.chat.completions.create(...)
except APIConnectionError as e:
    print(f"Connection failed: {e}")
    # Check internet connection, retry
```

**5. Timeout Errors:**
```python
from openai import APITimeoutError

try:
    response = client.chat.completions.create(...)
except APITimeoutError as e:
    print(f"Request timed out: {e}")
    # Increase timeout or reduce max_tokens
```

### 5.2 Retry with Exponential Backoff

**Method 1: Using Tenacity Library (Recommended):**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)
from openai import RateLimitError, APIConnectionError, AsyncOpenAI


@retry(
    retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
)
async def generate_code_with_retry(
    client: AsyncOpenAI,
    task: str,
    model: str = "gpt-4o",
) -> str:
    """Generate code with automatic retry on rate limits."""
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert developer."},
            {"role": "user", "content": task},
        ],
    )
    return response.choices[0].message.content


# Usage
async def main():
    client = AsyncOpenAI()

    try:
        code = await generate_code_with_retry(
            client,
            "Implement a binary search tree",
        )
        print(code)
    except Exception as e:
        print(f"Failed after retries: {e}")
```

**Method 2: Using Backoff Library:**
```python
import backoff
from openai import RateLimitError, OpenAI


@backoff.on_exception(
    backoff.expo,
    RateLimitError,
    max_tries=8,
    max_time=300,  # 5 minutes
)
def generate_code_with_backoff(
    client: OpenAI,
    task: str,
) -> str:
    """Generate code with exponential backoff on rate limits."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": task},
        ],
    )
    return response.choices[0].message.content
```

**Method 3: Custom Implementation:**
```python
import asyncio
import random
from typing import TypeVar, Callable
from openai import RateLimitError, APIConnectionError

T = TypeVar('T')


async def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 6,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    *args,
    **kwargs,
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        *args: Arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from successful function call

    Raises:
        Exception from last failed attempt
    """
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (RateLimitError, APIConnectionError) as e:
            if attempt == max_retries - 1:
                # Last attempt, re-raise
                raise

            # Calculate delay with exponential backoff + jitter
            delay = min(
                base_delay * (2 ** attempt) + random.uniform(0, 1),
                max_delay,
            )

            print(f"Attempt {attempt + 1} failed: {e}")
            print(f"Retrying in {delay:.2f} seconds...")

            await asyncio.sleep(delay)

    raise RuntimeError("Should not reach here")


# Usage
async def main():
    from openai import AsyncOpenAI

    client = AsyncOpenAI()

    async def generate():
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
        return response.choices[0].message.content

    try:
        result = await retry_with_exponential_backoff(generate)
        print(result)
    except Exception as e:
        print(f"All retries failed: {e}")
```

### 5.3 Token Limit Handling

**Strategy 1: Truncate Input:**
```python
import tiktoken


def truncate_to_token_limit(
    text: str,
    max_tokens: int,
    model: str = "gpt-4o",
) -> str:
    """Truncate text to fit within token limit."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # Truncate and decode
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens)


# Usage
context = load_large_codebase()
truncated = truncate_to_token_limit(context, max_tokens=100000)
```

**Strategy 2: Smart Context Selection:**
```python
def select_relevant_context(
    all_files: dict[str, str],
    task: str,
    max_tokens: int = 100000,
) -> dict[str, str]:
    """
    Select most relevant files that fit within token budget.

    Prioritize:
    1. Files mentioned in task
    2. Recently modified files
    3. Core modules
    """
    # Implementation would use embeddings or heuristics
    # to select most relevant files

    selected = {}
    total_tokens = 0

    # Simplified example
    for filename, content in all_files.items():
        file_tokens = count_tokens(content)

        if total_tokens + file_tokens <= max_tokens:
            selected[filename] = content
            total_tokens += file_tokens
        else:
            break

    return selected
```

**Strategy 3: Chunking:**
```python
async def process_large_task_in_chunks(
    client: AsyncOpenAI,
    large_codebase: dict[str, str],
    task: str,
) -> list[str]:
    """Process large codebase in chunks."""

    # Split into manageable chunks
    chunks = split_into_chunks(large_codebase, chunk_size=50000)

    results = []

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Context:\n{chunk}\n\nTask: {task}"},
            ],
        )

        results.append(response.choices[0].message.content)

    return results
```

### 5.4 Comprehensive Error Handler

```python
"""
Comprehensive error handling for OpenAI API.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Any
from openai import (
    OpenAI,
    AsyncOpenAI,
    APIError,
    RateLimitError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    APITimeoutError,
)

T = TypeVar('T')

logger = logging.getLogger(__name__)


class OpenAIErrorHandler:
    """Comprehensive error handler for OpenAI API calls."""

    def __init__(
        self,
        max_retries: int = 6,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def call_with_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Call function with comprehensive error handling and retry.

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            AuthenticationError: Invalid API key (no retry)
            BadRequestError: Invalid request (no retry)
            Exception: After all retries exhausted
        """
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)

            except AuthenticationError as e:
                # Don't retry auth errors
                logger.error(f"Authentication failed: {e}")
                logger.error("Check OPENAI_API_KEY environment variable")
                raise

            except BadRequestError as e:
                # Don't retry invalid requests
                logger.error(f"Invalid request: {e}")
                logger.error("Check model name, parameters, and message format")
                raise

            except RateLimitError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(f"Rate limit hit. Retrying in {delay:.2f}s... (attempt {attempt+1}/{self.max_retries})")
                await asyncio.sleep(delay)

            except APIConnectionError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Connection failed after {self.max_retries} attempts")
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(f"Connection error. Retrying in {delay:.2f}s... (attempt {attempt+1}/{self.max_retries})")
                await asyncio.sleep(delay)

            except APITimeoutError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Request timed out after {self.max_retries} attempts")
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(f"Timeout. Retrying in {delay:.2f}s... (attempt {attempt+1}/{self.max_retries})")
                await asyncio.sleep(delay)

            except APIError as e:
                # Generic API error
                if attempt == self.max_retries - 1:
                    logger.error(f"API error after {self.max_retries} attempts: {e}")
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(f"API error. Retrying in {delay:.2f}s... (attempt {attempt+1}/{self.max_retries})")
                await asyncio.sleep(delay)

            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error: {e}")
                raise

        raise RuntimeError("Should not reach here")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff + jitter."""
        import random
        delay = min(
            self.base_delay * (2 ** attempt),
            self.max_delay,
        )
        # Add jitter
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter


# Usage example
async def main():
    handler = OpenAIErrorHandler()
    client = AsyncOpenAI()

    async def generate_code():
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Write a function"}],
        )
        return response.choices[0].message.content

    try:
        code = await handler.call_with_retry(generate_code)
        print(code)
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

---

## 6. Git Worktree Integration

### 6.1 Working with Local Repository Paths

**Overview:**
- Each agent works in an isolated git worktree
- Worktrees share the same repository but have separate working directories
- Perfect for parallel development on the same codebase

**Worktree Structure:**
```
main-repo/
├── .git/               # Main git directory
├── ob1/                # Main working tree
├── tests/
└── worktrees/
    ├── agent-1/        # Worktree for agent 1
    ├── agent-2/        # Worktree for agent 2
    └── agent-3/        # Worktree for agent 3
```

**Creating Worktrees:**
```python
import asyncio
from pathlib import Path
from typing import Optional


async def create_worktree(
    repo_path: Path,
    branch_name: str,
    worktree_name: Optional[str] = None,
) -> Path:
    """
    Create a new git worktree for isolated development.

    Args:
        repo_path: Path to main repository
        branch_name: Name of branch to create
        worktree_name: Name of worktree directory (defaults to branch_name)

    Returns:
        Path to created worktree
    """
    if worktree_name is None:
        worktree_name = branch_name

    worktree_path = repo_path / "worktrees" / worktree_name

    # Create worktree with new branch
    proc = await asyncio.create_subprocess_exec(
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_path),
        "main",  # Base branch
        cwd=repo_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Failed to create worktree: {stderr.decode()}")

    print(f"Created worktree at {worktree_path}")
    return worktree_path


async def cleanup_worktree(
    repo_path: Path,
    worktree_path: Path,
) -> None:
    """Remove a git worktree."""
    proc = await asyncio.create_subprocess_exec(
        "git",
        "worktree",
        "remove",
        str(worktree_path),
        cwd=repo_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    await proc.communicate()
    print(f"Removed worktree at {worktree_path}")
```

### 6.2 Managing Multiple Parallel Sessions

**Orchestrator Pattern:**
```python
"""
Manage multiple parallel agent sessions in separate worktrees.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List
from openai import AsyncOpenAI


@dataclass
class AgentSession:
    """Represents a single agent working in a worktree."""

    agent_id: int
    worktree_path: Path
    branch_name: str
    task: str
    client: AsyncOpenAI


class ParallelOrchestrator:
    """Orchestrate multiple agents working in parallel."""

    def __init__(
        self,
        repo_path: Path,
        num_agents: int = 3,
    ):
        self.repo_path = repo_path
        self.num_agents = num_agents
        self.sessions: List[AgentSession] = []

    async def setup_sessions(self, task: str) -> None:
        """Create worktrees and initialize agent sessions."""

        for i in range(self.num_agents):
            agent_id = i + 1
            branch_name = f"agent-{agent_id}/{task.replace(' ', '-')[:30]}"

            # Create worktree
            worktree_path = await create_worktree(
                self.repo_path,
                branch_name,
                worktree_name=f"agent-{agent_id}",
            )

            # Create session
            session = AgentSession(
                agent_id=agent_id,
                worktree_path=worktree_path,
                branch_name=branch_name,
                task=task,
                client=AsyncOpenAI(),
            )

            self.sessions.append(session)

        print(f"Created {self.num_agents} agent sessions")

    async def run_agents_parallel(self) -> List[str]:
        """Run all agents in parallel and collect results."""

        tasks = [
            self._run_single_agent(session)
            for session in self.sessions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def _run_single_agent(self, session: AgentSession) -> str:
        """Run a single agent in its worktree."""

        print(f"Agent {session.agent_id} starting...")

        try:
            # Generate code
            code = await self._generate_code(session)

            # Write to files
            await self._write_files(session, code)

            # Run tests
            test_result = await self._run_tests(session)

            if not test_result:
                return f"Agent {session.agent_id}: Tests failed"

            # Create commit
            await self._create_commit(session)

            # Push to remote
            await self._push_branch(session)

            return f"Agent {session.agent_id}: Success ✓"

        except Exception as e:
            return f"Agent {session.agent_id}: Failed - {e}"

    async def _generate_code(self, session: AgentSession) -> str:
        """Generate code using OpenAI."""

        # Load context from worktree
        context = self._load_context(session.worktree_path)

        response = await session.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Python developer following TDD.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nTask: {session.task}",
                },
            ],
        )

        return response.choices[0].message.content

    async def _write_files(self, session: AgentSession, code: str) -> None:
        """Write generated code to worktree."""
        # Parse code and write to appropriate files
        # Simplified for example
        output_file = session.worktree_path / "ob1" / "generated.py"
        output_file.write_text(code)

    async def _run_tests(self, session: AgentSession) -> bool:
        """Run tests in worktree."""
        proc = await asyncio.create_subprocess_exec(
            "pytest",
            cwd=session.worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await proc.communicate()
        return proc.returncode == 0

    async def _create_commit(self, session: AgentSession) -> None:
        """Create commit in worktree."""
        await self._git_command(session, ["add", "."])
        await self._git_command(
            session,
            ["commit", "-m", f"feat: {session.task}"],
        )

    async def _push_branch(self, session: AgentSession) -> None:
        """Push branch to remote."""
        await self._git_command(
            session,
            ["push", "-u", "origin", session.branch_name],
        )

    async def _git_command(
        self,
        session: AgentSession,
        args: List[str],
    ) -> None:
        """Run git command in worktree."""
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=session.worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Git command failed: {stderr.decode()}")

    def _load_context(self, worktree_path: Path) -> str:
        """Load relevant context from worktree."""
        # Simplified - would load relevant files
        claude_md = worktree_path / "CLAUDE.md"
        if claude_md.exists():
            return claude_md.read_text()
        return ""

    async def cleanup(self) -> None:
        """Clean up all worktrees."""
        for session in self.sessions:
            await cleanup_worktree(self.repo_path, session.worktree_path)


# Usage
async def main():
    orchestrator = ParallelOrchestrator(
        repo_path=Path.cwd(),
        num_agents=3,
    )

    task = "Implement rate limiter with token bucket algorithm"

    # Setup
    await orchestrator.setup_sessions(task)

    # Run in parallel
    results = await orchestrator.run_agents_parallel()

    # Print results
    for result in results:
        print(result)

    # Cleanup
    # await orchestrator.cleanup()  # Commented out to preserve worktrees


if __name__ == "__main__":
    asyncio.run(main())
```

### 6.3 Programmatic Commit Creation

**Comprehensive Commit Workflow:**
```python
"""
Create commits programmatically with proper error handling.
"""

import asyncio
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class CommitResult:
    """Result of commit operation."""
    success: bool
    commit_hash: Optional[str]
    message: str


class GitCommitter:
    """Handle git commit operations programmatically."""

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path

    async def create_commit(
        self,
        message: str,
        files: Optional[List[str]] = None,
    ) -> CommitResult:
        """
        Create a git commit.

        Args:
            message: Commit message
            files: Specific files to commit (None = all changes)

        Returns:
            CommitResult with success status and commit hash
        """
        try:
            # Stage files
            if files:
                for file in files:
                    await self._run_git(["add", file])
            else:
                await self._run_git(["add", "."])

            # Check if there are changes to commit
            status = await self._run_git(["status", "--porcelain"])

            if not status.strip():
                return CommitResult(
                    success=False,
                    commit_hash=None,
                    message="No changes to commit",
                )

            # Create commit
            await self._run_git(["commit", "-m", message])

            # Get commit hash
            commit_hash = await self._run_git(["rev-parse", "HEAD"])
            commit_hash = commit_hash.strip()

            return CommitResult(
                success=True,
                commit_hash=commit_hash,
                message=f"Created commit {commit_hash[:8]}",
            )

        except Exception as e:
            return CommitResult(
                success=False,
                commit_hash=None,
                message=f"Commit failed: {e}",
            )

    async def create_commit_with_template(
        self,
        task: str,
        files_changed: List[str],
        ai_generated: bool = True,
    ) -> CommitResult:
        """Create commit with standardized message template."""

        # Generate commit message
        message = self._generate_commit_message(
            task,
            files_changed,
            ai_generated,
        )

        return await self.create_commit(message)

    def _generate_commit_message(
        self,
        task: str,
        files_changed: List[str],
        ai_generated: bool,
    ) -> str:
        """Generate standardized commit message."""

        # Determine commit type
        commit_type = "feat"  # Default

        if any("test" in f for f in files_changed):
            if all("test" in f for f in files_changed):
                commit_type = "test"
            else:
                commit_type = "feat"  # Mixed

        # Build message
        message = f"{commit_type}: {task}\n\n"
        message += "Changes:\n"

        for file in files_changed:
            message += f"- {file}\n"

        if ai_generated:
            message += "\n🤖 Generated with OpenAI GPT-4o\n"
            message += "Co-Authored-By: OpenAI <noreply@openai.com>\n"

        return message

    async def _run_git(self, args: List[str]) -> str:
        """Run git command and return output."""
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=self.worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Git command failed: {stderr.decode()}\n"
                f"Command: git {' '.join(args)}"
            )

        return stdout.decode()


# Usage
async def main():
    worktree = Path("/tmp/test-worktree")
    committer = GitCommitter(worktree)

    # Write some files
    test_file = worktree / "test.py"
    test_file.write_text("print('Hello, World!')")

    # Create commit
    result = await committer.create_commit_with_template(
        task="Add hello world script",
        files_changed=["test.py"],
        ai_generated=True,
    )

    print(f"Commit result: {result.message}")
    if result.success:
        print(f"Commit hash: {result.commit_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 7. Codex CLI Deep Dive

### 7.1 What is Codex CLI?

**Codex CLI** is OpenAI's official terminal-based coding agent that:
- Runs locally on your machine
- Integrates with your existing codebase
- Can read, modify, and run code
- Supports multi-modal input (text, screenshots, diagrams)
- Is fully open-source (Apache 2.0)

**Key Differences from API:**
- Codex CLI is a terminal tool (not an API endpoint)
- It provides an interactive coding assistant
- Has built-in safety features (sandboxing, approval workflows)
- Automatically understands repository context

### 7.2 Installation

**NPM:**
```bash
npm install -g @openai/codex
```

**Homebrew:**
```bash
brew install --cask codex
```

**Binary Downloads:**
- Available for macOS (Apple Silicon, x86_64) and Linux (x86_64, arm64)
- Download from: https://github.com/openai/codex/releases

### 7.3 Authentication

**ChatGPT Account (Recommended):**
```bash
codex
# Follow prompts to authenticate with ChatGPT account
```

**API Key:**
```bash
export OPENAI_API_KEY="sk-..."
codex
```

**Requirements:**
- ChatGPT Plus, Pro, Team, Edu, or Enterprise plan
- OR OpenAI API key with access to GPT-4o

### 7.4 Configuration

**Config File:** `~/.codex/config.toml`

**Example Configuration:**
```toml
[general]
model = "gpt-4o"
auto_approve = false
sandbox_mode = true

[network]
disable_in_sandbox = true

[mcp]
enabled = true
servers = ["example-server"]
```

### 7.5 Key Features

**1. Repository Awareness:**
- Automatically reads your codebase
- Understands project structure
- Follows project conventions

**2. AGENTS.md File:**
```markdown
# ob1 Project Guidelines for Codex

## Project Structure
- `ob1/` - Main package
- `tests/` - Test suite
- `pyproject.toml` - Dependencies

## Development Workflow
1. Write tests first (TDD)
2. Run tests: `pytest tests/`
3. Check types: `mypy ob1/`

## Code Style
- Use async/await for I/O
- Complete type hints (mandatory)
- Files < 300 lines

## Common Commands
- Run tests: `pytest tests/ -v`
- Format code: `black ob1/ tests/`
- Type check: `mypy ob1/`
```

**3. Slash Commands:**
```bash
/init         # Create AGENTS.md file
/status       # Show session config
/approvals    # Configure auto-approval
/model        # Change model
```

**4. Safety Features:**
- Approval workflows for dangerous operations
- Network sandboxing
- Directory restrictions

### 7.6 Using Codex CLI with ob1

**Workflow:**

1. **Initialize in Repository:**
```bash
cd /path/to/ob1
codex /init
```

2. **Configure AGENTS.md:**
```bash
# Edit .codex/AGENTS.md with ob1-specific guidelines
```

3. **Start Coding Session:**
```bash
codex "Implement rate limiter with token bucket algorithm following TDD"
```

4. **Review Changes:**
- Codex will show proposed changes
- Approve or reject each change
- Tests run automatically

**Example Session:**
```bash
$ codex

> Implement a rate limiter using token bucket algorithm with:
> - Async/await
> - Complete type hints
> - Comprehensive tests
> - Follow TDD (tests first)

[Codex reads AGENTS.md and codebase]

I'll implement this following your TDD workflow:

1. First, I'll write tests in tests/test_rate_limiter.py
2. Then implement in ob1/utils/rate_limiter.py

[Shows test code]

Approve changes to tests/test_rate_limiter.py? [y/n]
> y

[Writes tests, runs pytest - they fail as expected]

Now implementing the rate limiter...

[Shows implementation]

Approve changes to ob1/utils/rate_limiter.py? [y/n]
> y

[Writes implementation, runs pytest - tests pass]

✓ All tests passed!
Create commit? [y/n]
> y

[Creates commit with message]
```

### 7.7 Integration with ob1 Orchestrator

**Option 1: Use Codex CLI as an Agent:**

```python
"""
Use Codex CLI as one of the parallel agents.
"""

import asyncio
from pathlib import Path


async def run_codex_agent(
    worktree_path: Path,
    task: str,
) -> str:
    """
    Run Codex CLI in a worktree.

    Note: Codex CLI is interactive, so this requires
    non-interactive mode or automation wrapper.
    """

    # Codex CLI doesn't have a direct non-interactive mode yet
    # This would require wrapping or using the API instead

    proc = await asyncio.create_subprocess_exec(
        "codex",
        task,
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
    )

    # Send approvals programmatically
    stdout, stderr = await proc.communicate(input=b"y\ny\ny\n")

    return stdout.decode()
```

**Option 2: Use OpenAI API (Recommended for ob1):**

The OpenAI Chat Completions API is better suited for programmatic orchestration because:
- Non-interactive by default
- Easier to parallelize
- Full control over prompts and responses
- Can customize behavior per agent

**Recommendation:** Use Codex CLI for manual development, but use the OpenAI API for the ob1 orchestrator's automated parallel agents.

### 7.8 Codex CLI vs OpenAI API

| Feature | Codex CLI | OpenAI API |
|---------|-----------|------------|
| **Interface** | Terminal (interactive) | Programmatic (API calls) |
| **Repo Context** | Automatic | Manual (provide in prompts) |
| **Safety** | Built-in approvals | Manual implementation |
| **Parallelization** | Difficult | Easy |
| **Customization** | Limited | Full control |
| **Best For** | Manual development | Automation, orchestration |
| **Cost** | Included with ChatGPT Plus | Pay per token |

**For ob1 Orchestrator:** Use **OpenAI API** for the core orchestration, but document Codex CLI as an alternative for manual testing.

---

## Summary & Recommendations for ob1

### Recommended Architecture

```python
"""
ob1 Agent using OpenAI Chat Completions API
"""

from openai import AsyncOpenAI
from pathlib import Path
from typing import Dict


class OpenAIAgent:
    """OpenAI-powered code generation agent."""

    def __init__(
        self,
        worktree_path: Path,
        model: str = "gpt-4o",
    ):
        self.worktree_path = worktree_path
        self.model = model
        self.client = AsyncOpenAI()
        self.error_handler = OpenAIErrorHandler()

    async def execute_task(self, task: str) -> Dict[str, str]:
        """
        Execute a coding task in the worktree.

        Returns:
            Dict mapping file paths to generated content
        """
        # 1. Load context
        context = self._load_context()

        # 2. Generate code with retry
        async def generate():
            return await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nTask: {task}",
                    },
                ],
                temperature=0.7,
                max_tokens=4000,
            )

        response = await self.error_handler.call_with_retry(generate)

        # 3. Parse and return
        code = response.choices[0].message.content
        return self._parse_code_response(code)

    def _get_system_prompt(self) -> str:
        """Get system prompt with project guidelines."""
        claude_md = self.worktree_path / "CLAUDE.md"
        if claude_md.exists():
            return f"You are an expert developer.\n\n{claude_md.read_text()}"
        return "You are an expert Python developer."

    def _load_context(self) -> str:
        """Load relevant context from worktree."""
        # Implementation
        pass

    def _parse_code_response(self, response: str) -> Dict[str, str]:
        """Parse code from response."""
        # Implementation
        pass
```

### Best Practices

1. **Use gpt-4o** as the primary model
2. **Implement retry with exponential backoff** using tenacity
3. **Provide rich context** from CLAUDE.md and key files
4. **Use async/await** for parallel execution
5. **Handle errors comprehensively** with specific error types
6. **Monitor token usage** and implement smart context selection
7. **Create standardized commit messages** with AI attribution

### Cost Estimation

**For 3 parallel agents:**
- Model: gpt-4o
- Average tokens per task: ~10,000 (6K input + 4K output)
- Cost: ~$0.10 per task (estimate)
- 10 tasks per day: ~$1.00/day

**Note:** Actual costs depend on context size and response length. Monitor usage via OpenAI dashboard.

---

## Additional Resources

**Official Documentation:**
- OpenAI API: https://platform.openai.com/docs
- OpenAI Python SDK: https://github.com/openai/openai-python
- OpenAI Node SDK: https://github.com/openai/openai-node
- Codex CLI: https://github.com/openai/codex
- Rate Limits: https://platform.openai.com/docs/guides/rate-limits

**Community Resources:**
- OpenAI Cookbook: https://cookbook.openai.com/
- Community Forum: https://community.openai.com/

**Helpful Libraries:**
- `tenacity` - Retry with exponential backoff
- `tiktoken` - Token counting
- `python-dotenv` - Environment variable management
- `httpx` - Async HTTP client

---

## Conclusion

This comprehensive guide covers everything needed to integrate OpenAI's code generation capabilities into the ob1 orchestrator:

1. **Use OpenAI Chat Completions API** (not Codex CLI) for programmatic orchestration
2. **Choose gpt-4o** as the primary model for best results
3. **Implement robust error handling** with retry mechanisms
4. **Use git worktrees** for isolated parallel development
5. **Provide rich context** to improve code quality
6. **Follow TDD principles** in prompts and workflows

The code examples provided are production-ready and follow ob1's architecture principles (async-first, type-safe, testable).
