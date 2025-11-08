# GitHub Copilot & Codex Programmatic Access Research

**Research Date:** November 9, 2025
**Purpose:** Comprehensive analysis of GitHub Copilot and OpenAI Codex programmatic access for the ob1 parallel AI SWE orchestrator project.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [GitHub Copilot Overview](#github-copilot-overview)
3. [Programmatic Access Options](#programmatic-access-options)
4. [OpenAI Codex Status](#openai-codex-status)
5. [Integration Methods](#integration-methods)
6. [Capabilities](#capabilities)
7. [Pricing & Access](#pricing--access)
8. [Alternatives & Workarounds](#alternatives--workarounds)
9. [Recommendations for ob1](#recommendations-for-ob1)
10. [References](#references)

---

## Executive Summary

**Key Findings:**

- **No Official API:** GitHub Copilot does NOT provide a public API for programmatic code generation as of November 2025
- **Management APIs Only:** Only metrics/management REST APIs are available (usage stats, subscription management)
- **Codex Deprecated:** OpenAI's original Codex API was deprecated in March 2023; replaced by GPT-3.5/GPT-4
- **CLI Available:** GitHub Copilot CLI supports headless automation with approval controls
- **Unofficial Solutions Exist:** Reverse-engineered proxies and LSP integrations available (risky, unsupported)
- **Extensions Platform:** GitHub Copilot Extensions provide controlled integration but are being deprecated in favor of MCP

**Bottom Line for ob1:**
Direct programmatic access to GitHub Copilot for automated code generation is not officially supported and would require unofficial workarounds that violate GitHub's terms of service.

---

## 1. GitHub Copilot Overview

### Current Capabilities

GitHub Copilot is an AI-powered coding assistant that provides:

- **Code Completion:** Inline code suggestions as you type
- **Chat Interface:** Natural language conversations about code
- **Code Review:** Automated PR reviews with contextual feedback
- **Terminal Commands:** CLI integration for command suggestions
- **PR Summaries:** Automated pull request descriptions
- **Coding Agent:** Autonomous task completion in GitHub Actions environments

### Models Used (2025)

GitHub Copilot currently uses multiple AI models:

| Feature | Default Model | Alternative Models |
|---------|---------------|-------------------|
| **Code Completion** | GPT-4o Copilot (specialized) | GPT-4.1 |
| **Chat** | GPT-4.1 | GPT-4o, Claude 3.5 Sonnet, GPT-5 (preview), o3 (preview), o4-mini (preview) |
| **CLI** | Claude Sonnet 4 | Claude Sonnet 4.5 (v0.0.329+) |
| **Agent Mode** | GPT-4.1 | Various via model picker |

**Model Evolution:**
- **2021-2023:** OpenAI Codex (modified GPT-3)
- **2023:** Upgraded to GPT-4 for chat
- **2024:** Multi-model support introduced
- **2025:** GPT-4.1 default, GPT-4o code completion model

**Source:** [Which AI model should I use with GitHub Copilot?](https://github.blog/ai-and-ml/github-copilot/which-ai-model-should-i-use-with-github-copilot/)

### Product Variants

1. **GitHub Copilot (IDE):** VS Code, Visual Studio, JetBrains, Neovim, Xcode
2. **GitHub Copilot Chat:** Conversational AI in IDE + GitHub.com
3. **GitHub Copilot CLI:** Terminal-based assistance (`gh copilot`)
4. **GitHub Copilot for Pull Requests:** Automated PR summaries and reviews
5. **GitHub Copilot Coding Agent:** Autonomous SWE agent in GitHub Actions

---

## 2. Programmatic Access Options

### 2.1 Official REST API (Limited)

**Available Endpoints:**

```
GET /orgs/{org}/copilot/metrics
GET /orgs/{org}/team/{team_slug}/copilot/metrics
```

**Authentication:**
- OAuth app tokens
- Personal access tokens (classic) with `manage_billing:copilot`, `read:org`, or `read:enterprise` scopes
- GitHub App tokens
- Fine-grained PATs with "GitHub Copilot Business" or "Administration" organization read permissions

**Data Provided:**
- Active user counts
- Code completion statistics (suggestions, acceptances, lines of code)
- Chat usage metrics
- PR summary generation data
- Language and editor breakdowns
- Custom model performance metrics

**Limitations:**
- **Metrics only** - no code generation capabilities
- Requires 5+ members with active Copilot licenses
- Data aggregated daily (previous day)
- Maximum 100 days of history

**Status:** Public preview (announced October 2025)

**Documentation:** [REST API endpoints for Copilot metrics](https://docs.github.com/en/rest/copilot/copilot-metrics)

### 2.2 GitHub Copilot CLI

**Installation:**

```bash
# Install GitHub CLI
brew install gh  # macOS
# or see https://cli.github.com/

# Install Copilot extension
gh extension install github/gh-copilot

# Or install standalone (npm)
npm install -g @github/copilot-cli
```

**Interactive Mode:**

```bash
copilot
# Opens interactive session
```

**Programmatic Mode:**

```bash
# Single prompt
copilot -p "write a python function to reverse a string"

# Piped input
echo "explain this git command: git rebase -i HEAD~3" | copilot
```

**Headless Automation:**

```bash
# Allow all tools automatically (DANGEROUS)
copilot --allow-all-tools -p "create a new feature branch"

# Selective tool approval
copilot --allow-tool 'shell(git)' --allow-tool 'write' -p "commit all changes"

# Block specific commands
copilot --allow-all-tools --deny-tool 'shell(rm)' -p "clean up temp files"

# Scoped git commands
copilot --allow-tool 'shell(git push)' -p "push to origin"
```

**Capabilities:**

| Category | Capabilities |
|----------|-------------|
| **Local** | Modify code, review changes, create apps, debug, improve docs |
| **Git** | Commits, reverts, branch operations (with subcommand granularity) |
| **GitHub** | Fetch PRs/issues, create PRs, merge, close, raise issues |
| **CI/CD** | Create GitHub Actions workflows, find workflow types |

**Security Considerations:**

- **Trusted Directories:** Must confirm trust in launch directory
- **Scoped Permissions:** Heuristic (NOT guaranteed comprehensive)
- **Mitigation:** Use in VM/container/isolated environment for automatic approval
- **Account Risk:** Excessive automation may trigger GitHub abuse detection

**Quota:**
- Each prompt reduces monthly premium request quota by one
- Uses Copilot premium request allowance

**Platform Support:**
- Linux, macOS, Windows (via WSL)
- Native PowerShell support is experimental

**Documentation:** [About GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli)

### 2.3 Copilot Language Server (Official SDK)

**Package:** `@github/copilot-language-server`

**Installation:**

```bash
npm install @github/copilot-language-server
```

**Running:**

```bash
# Platform-specific binaries included
./node_modules/@github/copilot-language-server-darwin-arm64/copilot-language-server --stdio
```

**Protocol:** Language Server Protocol (LSP) over JSON-RPC 2.0

**Custom LSP Extensions:**
- `textDocument/inlineCompletion` - Retrieve inline completions
- `textDocument/didShowCompletion` - Acceptance telemetry
- `textDocument/didFocus` - Document focus notification
- `signInInitiate` / `signInConfirm` - Device flow authentication
- `conversation/create` / `conversation/turn` - Chat integration

**Basic Flow:**

```
1. initialize request (LSP spec)
2. workspace/didChangeConfiguration notification
3. signIn for authentication (device flow)
4. textDocument/didOpen to register documents
5. getCompletions for suggestions
```

**Authentication:**
- GitHub OAuth with Copilot's App ID
- Device flow authentication
- Requires prior authentication or programmatic sign-in

**Use Cases:**
- Custom editor/IDE integration
- Building Copilot-like features
- Automating code suggestions

**Status:** Generally available (announced February 2025)

**Documentation:** [Copilot Language Server SDK](https://github.blog/changelog/2025-02-10-copilot-language-server-sdk-is-now-available/)

### 2.4 VS Code Extension APIs

**Language Model API:**

Provides direct programmatic access to AI models within VS Code extensions:

```javascript
// Access language models
const models = await vscode.lm.selectChatModels();
const response = await models[0].sendRequest(messages);
```

**Capabilities:**
- Direct access to Copilot's underlying models
- Integration into custom extension features
- Code actions, hover providers, custom views
- Full access to VS Code extension APIs

**Chat Extension API:**

Create custom chat participants:

```javascript
// Register chat participant
const participant = vscode.chat.createChatParticipant('myBot', handler);
```

**Capabilities:**
- Custom @-mention participants in Copilot Chat
- Context-aware responses
- Local workspace access
- File read/write operations
- VS Code UI manipulation

**Limitations:**
- **VS Code only** - not cross-IDE
- Requires user to have Copilot subscription
- Extensions run client-side
- No standalone API access

**Documentation:** [AI extensibility in VS Code](https://code.visualstudio.com/docs/copilot/copilot-extensibility-overview)

### 2.5 GitHub Copilot Extensions (DEPRECATED)

**Status:** DEPRECATED as of September 23, 2025, shutdown November 10, 2025

**Replacement:** Model Context Protocol (MCP) servers

**Historical Context:**

GitHub Copilot Extensions were GitHub Apps that integrated external tools with Copilot Chat:

- **Skillsets:** Lightweight, automated routing and prompt crafting
- **Agents:** Full control, custom logic, multi-LLM integration

**Migration Path:** Build MCP servers instead

**Documentation:** [About building GitHub Copilot Extensions](https://docs.github.com/en/copilot/concepts/extensions/build-extensions)

### 2.6 Model Context Protocol (MCP)

**What is MCP?**

An open standard for sharing context between applications and LLMs, replacing Copilot Extensions.

**Supported IDEs:**
- Visual Studio Code (1.99+)
- Visual Studio (17.14+)
- JetBrains IDEs
- Eclipse (2024-09+)
- Xcode

**Configuration Methods:**

1. **GitHub MCP Registry:** Browse and install curated servers
2. **Manual Configuration:**
   - Repository-level: `.vscode/mcp.json`
   - User-level: IDE settings

**Server Types:**

| Type | Hosting | Authentication |
|------|---------|----------------|
| **Remote** | HTTP/SSE | OAuth or PAT |
| **Local** | Command-line | N/A |

**Example MCP Servers:**
- **Fetch:** Web content retrieval
- **Memory:** Data persistence
- **GitHub:** Repository and issue management

**Usage:**

```bash
# Reference MCP prompts
/mcp.servername.promptname

# Access tools via chat interface tools icon
# Add MCP resources via "Add Context" menu
```

**Capabilities:**
- Query third-party services
- Execute external actions
- Fetch documentation
- Access databases
- Custom tool integration

**Documentation:** [Extending GitHub Copilot Chat with MCP](https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol/extending-copilot-chat-with-mcp)

---

## 3. OpenAI Codex Status

### Original Codex API (2021-2023)

**Status:** DEPRECATED - March 23, 2023

**Timeline:**
- **2021:** Codex released (code-optimized GPT-3)
- **March 23, 2023:** API deprecated
- **Replacement:** GPT-3.5-turbo and GPT-4

**Migration Path:**
- Switch to GPT-3.5-turbo or GPT-4 via OpenAI API
- GitHub Copilot migrated to GPT-4

**Source:** [OpenAI kills its Codex code model](https://the-decoder.com/openai-kills-code-model-codex/)

### New Codex (2025)

**Status:** ACTIVE - Different product entirely

**What is it?**
An autonomous software engineering agent (not an API), available in ChatGPT.

**Capabilities:**
- Cloud-based parallel task execution
- CLI tool with autonomous coding
- Available to ChatGPT Plus and Pro users
- On-demand credits for additional usage

**Key Differences:**

| Feature | Old Codex (2021) | New Codex (2025) |
|---------|------------------|------------------|
| **Type** | API endpoint | Autonomous agent |
| **Access** | Direct API calls | ChatGPT interface / CLI |
| **Model** | Modified GPT-3 | Latest GPT models |
| **Status** | Deprecated | Active |

**Documentation:** [OpenAI Codex: From 2021 Code Model to a 2025 Autonomous Coding Agent](https://medium.com/@aliazimidarmian/openai-codex-from-2021-code-model-to-a-2025-autonomous-coding-agent-85ef0c48730a)

**Bottom Line:** The original Codex API no longer exists. Use OpenAI's GPT-3.5/GPT-4 APIs instead.

---

## 4. Integration Methods

### 4.1 Official Methods

| Method | Use Case | Automation Level | Risk |
|--------|----------|------------------|------|
| **Copilot CLI** | Terminal commands, Git operations, simple automation | Medium (with approval controls) | Low (official) |
| **VS Code Extension API** | Custom IDE features, chat participants | Low (user-initiated) | Low (official) |
| **MCP Servers** | Tool/service integration, context sharing | Medium | Low (official) |
| **Language Server SDK** | Custom editor integration | High (full LSP control) | Low (official) |
| **REST API** | Metrics and management | None (read-only) | Low (official) |

### 4.2 Unofficial Methods (HIGH RISK)

#### Reverse-Engineered Proxies

**Projects:**

1. **copilot-api** (ericc-ch)
   - **URL:** https://github.com/ericc-ch/copilot-api
   - **Function:** Converts Copilot to OpenAI/Anthropic-compatible API
   - **Endpoints:** `/v1/chat/completions`, `/v1/messages`
   - **Usage:** `npx copilot-api@latest start`
   - **Docker:** `docker run -v ~/.copilot-api:/root/.copilot-api -p 4141:4141 ericcchiu/copilot-api`

2. **gh_copilot_chat** (rabilrbl)
   - **URL:** https://github.com/rabilrbl/gh_copilot_chat
   - **Language:** Python
   - **Type:** Unofficial SDK (reverse engineered)

3. **copilot-explorer** (thakkarparth007)
   - **URL:** https://github.com/thakkarparth007/copilot-explorer
   - **Purpose:** Analyze what Copilot extension sends to server
   - **Blog:** [Copilot Internals](https://thakkarparth007.github.io/copilot-explorer/posts/copilot-internals.html)

**How They Work:**

1. Intercept Copilot authentication (OAuth device flow)
2. Proxy API calls to GitHub's internal endpoints
3. Re-expose as OpenAI/Anthropic-compatible endpoints
4. Handle token refresh automatically

**Technical Details:**

```javascript
// Example: OpenAI-compatible endpoint
POST http://localhost:4141/v1/chat/completions
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "write a Python function"}]
}

// Example: Anthropic-compatible endpoint
POST http://localhost:4141/v1/messages
{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [{"role": "user", "content": "explain this code"}]
}
```

**CRITICAL WARNINGS:**

1. **Not Supported by GitHub:** May break unexpectedly
2. **Terms of Service Violation:** "Excessive automated or scripted use" prohibited
3. **Account Suspension Risk:** GitHub's abuse-detection systems may flag usage
4. **No Guarantees:** Reverse-engineered, subject to change
5. **Security Risk:** Unofficial authentication handling

**GitHub's Policy (from search results):**
> "Excessive automated or scripted use of Copilot (including rapid or bulk requests, such as via automated tools) may trigger GitHub's abuse-detection systems. You may receive a warning from GitHub Security, and further anomalous activity could result in temporary suspension of your Copilot access."

**Blog Reference:** [I Turned GitHub Copilot Into OpenAI Compatible API Provider](https://ericc-ch.github.io/blog/reverse-engineering-copilot-api/)

#### Direct LSP Access (Reverse Engineering)

**Methods:**

1. **copilot.vim approach:**
   - Uses JSON-RPC API
   - Logging: `~/copilot-prompts.log`, `~/copilot-suggestions.log`
   - Requires parsing JSON-RPC output

2. **copilot.lua:**
   - **URL:** https://github.com/zbirenbaum/copilot.lua
   - Full-featured replacement for copilot.vim
   - Includes API for interacting with Copilot

3. **copilot.el:**
   - **URL:** https://github.com/copilot-emacs/copilot.el
   - Unofficial Emacs plugin
   - Uses official `@github/copilot-language-server`

**Technical Flow:**

```
1. Initialize LSP connection (JSON-RPC over stdio)
2. Send initialize request with capabilities
3. Authenticate via signInInitiate/signInConfirm
4. Register documents with textDocument/didOpen
5. Request completions with custom getCompletions method
6. Parse JSON-RPC responses
```

**Resources:**
- [Reverse Engineering Github Copilot](https://bootk.id/posts/copilot/)
- [How to invoke Github Copilot programmatically?](https://stackoverflow.com/questions/76741410/how-to-invoke-github-copilot-programmatically)

### 4.3 GitHub Actions Integration

**Copilot Coding Agent in GitHub Actions:**

GitHub's official approach to automation:

- **Environment:** Secure, ephemeral dev environments powered by GitHub Actions
- **Workflow:** Assign issues → Agent explores repo → Writes code → Passes tests → Opens PR
- **Customization:** 25,000+ community actions available
- **Use Case:** Autonomous SWE agent, not general-purpose API

**CI/CD Integration Methods:**

1. **Automated Code Review:**
   - Configure in branch rules: "Automatically request Copilot code review"
   - Reviews all pushes or once per PR
   - Identifies risky diffs, missing coverage, bugs

2. **PR Summaries:**
   - Automatic PR description generation
   - Change impact analysis
   - Reviewer focus areas

3. **Workflow Generation:**
   - Ask Copilot CLI to create GitHub Actions workflows
   - Example: `copilot -p "create a CI workflow for Python with pytest"`

**Documentation:**
- [GitHub Copilot coding agent 101](https://github.blog/ai-and-ml/github-copilot/github-copilot-coding-agent-101-getting-started-with-agentic-workflows-on-github/)
- [Integrating GitHub Copilot with CI/CD Pipelines](https://www.amplifilabs.com/post/integrating-github-copilot-with-ci-cd-pipelines-for-smarter-automation)

---

## 5. Capabilities

### 5.1 Code Generation

**Methods:**
- **IDE:** Inline completions, multi-line suggestions
- **Chat:** Conversational code generation
- **CLI:** Terminal-based code generation with approval

**Supported Languages:** 30+ (Python, JavaScript, TypeScript, Go, Rust, Java, C++, etc.)

**Context Window:**
- GPT-4.1: ~128K tokens
- GPT-4o: ~128K tokens
- Claude Sonnet 4: 200K tokens standard, 1M tokens in beta

### 5.2 Code Completion

**Model:** GPT-4o Copilot (specialized for code completion)

**Features:**
- Multi-line completions
- Context-aware suggestions
- 275,000+ high-quality repositories training data
- Real-time as-you-type suggestions

**Metrics (from API):**
- Suggestion counts
- Acceptance rates
- Lines of code accepted

### 5.3 Chat-Based Code Editing

**Platforms:**
- IDE chat interface (@copilot)
- GitHub.com chat (Copilot Pro+/Enterprise)
- CLI conversational mode

**Capabilities:**
- Explain code
- Generate tests
- Refactor code
- Debug issues
- Answer technical questions
- Propose architectural changes

### 5.4 Terminal Command Suggestions

**GitHub CLI Integration:**

```bash
# Command suggestion
gh copilot suggest
# Aliases: ghcs (after running gh copilot alias)

# Command explanation
gh copilot explain
# Aliases: ghce

# Specify command type
gh copilot suggest -t git     # Git commands
gh copilot suggest -t gh      # GitHub CLI commands
gh copilot suggest -t generic # Any shell command
```

**Features:**
- Interactive command refinement
- Execution, explanation, or copy options
- Revision capability

### 5.5 PR Summaries

**Automatic Generation:**
- Overview of changes in prose
- Bulleted list of changes with file impacts
- Reviewer focus areas
- Links to specific lines of code

**Configuration:**
- Per-repository settings
- Automatic vs. manual generation
- Draft PR support

**Metrics Tracked:**
- PR summary generation counts
- Usage across organization

### 5.6 Code Review

**Features (Public Preview - October 2025):**

- **Full Context:** Gathers entire project context for reviews
- **CodeQL Integration:** Deterministic detections
- **Automated Fixes:** @copilot mentions trigger fix suggestions in stacked PRs
- **Branch Rules:** Automatic review on new pushes
- **Risk Detection:** Identifies risky diffs, missing test coverage, bugs

**Configuration:**
- Branch protection rules integration
- Review all pushes or once per PR
- Draft PR review support

**Plans:** Copilot Pro, Pro+, Business, Enterprise

**Documentation:** [About GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review)

---

## 6. Pricing & Access

### 6.1 Subscription Tiers (2025)

| Plan | Price | Premium Requests | Models | Best For |
|------|-------|------------------|--------|----------|
| **Free** | $0 | 50/month | Limited | Trial/light use |
| **Pro** | $10/month or $100/year | 300/month | GPT-4.1, GPT-4o | Individual developers |
| **Pro+** | $19-39/month | 1,500/month | All models (GPT-5, o3, o4-mini) | Power users |
| **Business** | $19/user/month | 300/month | All models | Teams |
| **Enterprise** | $39/user/month | 1,000/month | All models + custom | Organizations |

**Sources:**
- [GitHub Copilot Plans & Pricing](https://github.com/features/copilot/plans)
- [GitHub Copilot Pricing 2025: Complete Cost Analysis](https://skywork.ai/blog/agent/github-copilot-pricing-2025-complete-cost-analysis-roi-calculator/)

### 6.2 Premium Requests

**What are Premium Requests?**

Requests using models other than the base model (GPT-4o) count as "premium requests":

- Claude 3.5 Sonnet
- Claude 3.7 Sonnet
- GPT-5 (preview)
- o3 (preview)
- o4-mini (preview)

**Quota Details:**
- Counters reset 1st of each month at 00:00 UTC
- Additional requests: $0.04 per request
- Default budget for old accounts: $0 (must opt-in)

**Billing Start Dates:**
- **GitHub.com:** June 18, 2025
- **GHE.com:** August 1, 2025

### 6.3 Rate Limits

**Dynamic Rate Limiting:**
- Normal human-paced coding rarely hits limits
- Heavy automated prompting triggers throttling
- Individual plans more restrictive than Enterprise

**API Rate Limits:**
- Metrics API: Standard GitHub REST API limits apply
- No published limits for Copilot-specific endpoints

**CLI Limits:**
- Each CLI prompt consumes 1 premium request from quota
- No specific rate limits documented

### 6.4 Enterprise Requirements

**GitHub Copilot Business/Enterprise:**

- **Minimum:** 5+ members with active licenses (for metrics)
- **Organization Policy:** Admins can enable/disable features
- **MCP Server Policy:** Org/Enterprise must enable MCP
- **Data Processing:** Covered by Data Protection Agreement

**GitHub Enterprise Cloud Required for:**
- Custom models (Enterprise plan)
- Knowledge bases (Enterprise plan)
- GitHub.com Chat integration (Enterprise plan)

---

## 7. Alternatives & Workarounds

### 7.1 Direct API Alternatives

If GitHub Copilot API is unavailable, consider these programmatic alternatives:

#### Anthropic Claude API

**Access:** Pay-as-you-go API + subscription

**Pricing:**
- API: Per-token billing
- Claude Pro: ~$20/month (web interface)
- Claude Max: ~$200/month (higher limits)

**Models:**
- Claude 3.5 Sonnet
- Claude 3 Opus
- Claude 3 Haiku

**Context Window:** Up to 1M tokens (long-context beta)

**Code Capabilities:**
- Excellent code generation
- Multi-file editing
- Test generation
- Debugging

**API Documentation:** https://docs.anthropic.com/

**Integration:**
```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a Python function to..."}]
)
```

#### OpenAI GPT-4/GPT-4o API

**Access:** Pay-as-you-go API

**Pricing:**
- GPT-4: $30/1M input tokens, $60/1M output tokens
- GPT-4o: $5/1M input tokens, $15/1M output tokens
- GPT-3.5-turbo: $0.50/1M input, $1.50/1M output

**Models:**
- GPT-4o (latest)
- GPT-4 Turbo
- GPT-3.5-turbo
- o1 (reasoning model)

**Context Window:** 128K tokens

**API Documentation:** https://platform.openai.com/docs/api-reference

**Integration:**
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a Python function to..."}]
)
```

### 7.2 Alternative AI Coding Tools

#### Cursor

**Type:** AI-powered IDE (fork of VS Code)

**Pricing:**
- Free: Hobby tier (limited)
- Pro: $20/month
- Business: $40/user/month

**Models:**
- GPT-4o, o1
- Claude 3.5 Sonnet
- cursor-small (custom)

**Features:**
- Multi-file editing
- Codebase-aware chat
- Inline editing
- Terminal integration

**API Access:** None (IDE only)

**Website:** https://cursor.sh/

#### Aider

**Type:** AI pair programming in terminal

**Access:** Open source + API keys required

**Pricing:** Free (BYOK - Bring Your Own Key)

**Models:**
- Any OpenAI model
- Any Anthropic model
- Local models via Ollama

**Features:**
- Git integration
- Multi-file editing
- Automatic commits
- Works with any editor

**Repository:** https://github.com/paul-gauthier/aider

**Integration:**
```bash
pip install aider-chat
export ANTHROPIC_API_KEY=sk-ant-...
aider --model claude-3-5-sonnet-20241022
```

#### Cline (VS Code Extension)

**Type:** Autonomous coding agent in VS Code

**Access:** VS Code extension + API keys

**Pricing:** Free extension (BYOK)

**Models:**
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude 3.5)
- Local models

**Features:**
- Autonomous task execution
- File editing
- Terminal command execution
- Browser integration

**Marketplace:** https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev

### 7.3 Workarounds for Copilot Access

#### Option 1: Copilot CLI with Scripting

**Use Case:** Simple automation with user supervision

**Method:**
```bash
#!/bin/bash
# Automated PR creation with Copilot CLI

# Install jq for JSON parsing
# Use --allow-tool for controlled automation

copilot --allow-tool 'shell(git)' --allow-tool 'write' \
  -p "Create a feature branch, implement user authentication, commit changes"

# Capture output and parse
# Requires careful output handling
```

**Pros:**
- Official tool
- No API key management
- Uses existing Copilot subscription

**Cons:**
- Limited programmatic control
- Output parsing challenges
- Quota consumption (premium requests)
- Still requires human approval for safety

#### Option 2: Unofficial Proxy (HIGH RISK)

**Use Case:** Desperate need for API access (NOT RECOMMENDED)

**Method:**
```bash
# Install copilot-api proxy
npx copilot-api@latest start

# Use as OpenAI-compatible API
curl http://localhost:4141/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Generate code"}]
  }'
```

**Integration with Claude Code (per copilot-api docs):**
```bash
# Set environment variables
export ANTHROPIC_BASE_URL=http://localhost:4141/v1
export ANTHROPIC_API_KEY=dummy

# Claude Code will now use Copilot via proxy
```

**CRITICAL RISKS:**
1. **Account Suspension:** Violates GitHub ToS
2. **Unreliable:** May break without warning
3. **Security:** Unofficial authentication handling
4. **Legal:** Reverse engineering concerns

**Only Use If:**
- You understand and accept the risks
- No other option exists
- Limited, non-production testing
- Prepared for account suspension

#### Option 3: VS Code Extension API (Limited)

**Use Case:** VS Code-specific automation

**Method:**
```javascript
// In VS Code extension
const models = await vscode.lm.selectChatModels();
const response = await models[0].sendRequest([
  vscode.LanguageModelChatMessage.User("Generate a function...")
]);

// Stream response
for await (const chunk of response.text) {
  console.log(chunk);
}
```

**Pros:**
- Official API
- Access to Copilot models
- Full VS Code integration

**Cons:**
- VS Code only (not cross-platform)
- Requires user Copilot subscription
- Limited to extension context
- Not suitable for server-side automation

#### Option 4: Switch to Claude API

**Use Case:** Need reliable, programmatic access

**Recommendation:** Best alternative for ob1 project

**Method:**
```python
# Use Anthropic Claude API directly
import anthropic
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Generate code
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": "Implement user authentication in Python using FastAPI"
    }]
)

print(response.content[0].text)
```

**Pros:**
- Official, supported API
- Excellent code generation
- 200K-1M token context
- Predictable pricing
- No reverse engineering
- No account suspension risk

**Cons:**
- Additional cost ($0.003/1K input, $0.015/1K output for Sonnet)
- Not GitHub Copilot (different model)

---

## 8. Recommendations for ob1

### 8.1 Primary Recommendation: Claude API

**Why:**
- Official, stable API
- Superior code generation (Claude 3.5 Sonnet)
- Massive context window (200K-1M tokens)
- Predictable pricing
- No ToS violations
- Already integrated in Claude Code SDK

**Implementation:**
```python
from anthropic import Anthropic
import asyncio

class ClaudeAgent:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    async def generate_code(self, task: str, context: str) -> str:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": f"Task: {task}\n\nContext:\n{context}"
            }]
        )
        return response.content[0].text
```

**Cost Estimate (Claude 3.5 Sonnet):**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens
- Typical PR: ~10K tokens input, 5K tokens output = $0.105
- 100 parallel PRs: ~$10.50

### 8.2 Secondary Option: OpenAI GPT-4o API

**Why:**
- Similar to Copilot's underlying models
- Well-documented API
- Good code generation
- Competitive pricing

**Implementation:**
```python
from openai import AsyncOpenAI

class OpenAIAgent:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_code(self, task: str, context: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"Task: {task}\n\nContext:\n{context}"
            }]
        )
        return response.choices[0].message.content
```

**Cost Estimate (GPT-4o):**
- Input: $5 per 1M tokens
- Output: $15 per 1M tokens
- Typical PR: ~10K tokens input, 5K tokens output = $0.125
- 100 parallel PRs: ~$12.50

### 8.3 NOT Recommended: GitHub Copilot

**Why NOT:**

1. **No Official API:** No programmatic code generation API exists
2. **CLI Limitations:**
   - Designed for human interaction
   - Premium request quota consumption
   - Output parsing challenges
   - Not suitable for parallel automation
3. **Unofficial Methods Too Risky:**
   - Account suspension risk
   - ToS violations
   - Unreliable (may break)
   - Security concerns
4. **Wrong Use Case:** Copilot optimized for IDE, not automation

**Only Consider If:**
- Users already have Copilot subscriptions
- Willing to use Copilot CLI with manual supervision
- Accept limitations and quota consumption

### 8.4 Architecture Recommendation for ob1

**Multi-Agent Orchestrator Design:**

```python
from typing import Protocol, List
from dataclasses import dataclass

class AIAgent(Protocol):
    async def generate_pr(self, issue: str, context: str) -> PullRequest:
        ...

@dataclass
class AgentConfig:
    name: str
    agent_class: type
    api_key: str

class Orchestrator:
    def __init__(self, agents: List[AgentConfig]):
        self.agents = [
            config.agent_class(api_key=config.api_key)
            for config in agents
        ]

    async def create_parallel_prs(self, issue: str) -> List[PullRequest]:
        """Create competing PRs from multiple agents."""
        tasks = [
            agent.generate_pr(issue, self.get_context())
            for agent in self.agents
        ]
        return await asyncio.gather(*tasks)

# Usage
orchestrator = Orchestrator([
    AgentConfig("claude1", ClaudeAgent, os.getenv("ANTHROPIC_API_KEY")),
    AgentConfig("claude2", ClaudeAgent, os.getenv("ANTHROPIC_API_KEY")),
    AgentConfig("gpt4o", OpenAIAgent, os.getenv("OPENAI_API_KEY")),
])

prs = await orchestrator.create_parallel_prs("Add user authentication")
```

**Benefits:**
- Official APIs only
- No ToS violations
- Reliable, stable
- True parallel execution
- Model diversity (Claude + GPT-4o)
- Predictable costs

### 8.5 Feature Parity Matrix

| Feature | Claude API | OpenAI API | Copilot CLI | Copilot (Unofficial) |
|---------|------------|------------|-------------|----------------------|
| **Programmatic Access** | ✅ Official | ✅ Official | ⚠️ Limited | ❌ Reverse engineered |
| **Parallel Execution** | ✅ Yes | ✅ Yes | ❌ No | ⚠️ Risky |
| **Code Generation** | ✅ Excellent | ✅ Very Good | ✅ Good | ✅ Good |
| **Context Window** | ✅ 200K-1M | ✅ 128K | ⚠️ Unknown | ⚠️ Unknown |
| **Cost Predictability** | ✅ Pay-per-token | ✅ Pay-per-token | ⚠️ Quota-based | ⚠️ Unknown |
| **ToS Compliance** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Account Risk** | ✅ None | ✅ None | ✅ None | ❌ High |
| **Reliability** | ✅ SLA | ✅ SLA | ✅ Supported | ❌ May break |
| **Multi-file Editing** | ✅ Yes | ✅ Yes | ⚠️ Limited | ⚠️ Unknown |
| **Git Integration** | ⚠️ Manual | ⚠️ Manual | ✅ Built-in | ⚠️ Manual |

**Verdict:** Claude API or OpenAI API for ob1

---

## 9. Implementation Roadmap for ob1

### Phase 1: Foundation (Use Claude API)

**Goals:**
- Proof of concept with single agent
- Git worktree management
- PR creation automation

**Agent Choice:** Claude 3.5 Sonnet API

**Tasks:**
1. Implement `ClaudeAgent` class with Anthropic SDK
2. Test code generation quality
3. Implement Git worktree creation/management
4. Automate PR creation via GitHub API
5. Basic error handling and logging

### Phase 2: Parallel Orchestration

**Goals:**
- Multiple agents working in parallel
- Competing PR generation
- Result comparison

**Tasks:**
1. Implement `Orchestrator` class
2. Add OpenAI GPT-4o as second agent type
3. Parallel worktree creation
4. Concurrent PR generation
5. PR labeling/tagging by agent

### Phase 3: Advanced Features

**Goals:**
- Agent diversity
- Quality metrics
- Auto-testing
- Winner selection

**Tasks:**
1. Add more agent variations (different prompts, models)
2. Implement automated testing in each worktree
3. Collect metrics (test pass rate, code quality, coverage)
4. Winner selection algorithm
5. Automated PR merging/closing

### Phase 4 (Future): Copilot Integration

**Only if/when:**
- Official Copilot API is released
- OR Copilot CLI becomes more automation-friendly
- OR Willing to accept unofficial proxy risks for experimentation

**NOT Recommended for Production:**
- Unofficial proxy methods
- Extensive CLI scripting for parallel execution

---

## 10. References

### Official Documentation

1. **GitHub Copilot:**
   - [GitHub Copilot Concepts](https://docs.github.com/en/copilot/concepts)
   - [About GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli)
   - [Using GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli)
   - [REST API endpoints for Copilot metrics](https://docs.github.com/en/rest/copilot/copilot-metrics)
   - [About GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review)
   - [Extending Copilot Chat with MCP](https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol/extending-copilot-chat-with-mcp)

2. **VS Code:**
   - [AI extensibility in VS Code](https://code.visualstudio.com/docs/copilot/copilot-extensibility-overview)
   - [GitHub Copilot Extensions are all you need](https://code.visualstudio.com/blogs/2024/06/24/extensions-are-all-you-need)

3. **Language Server:**
   - [@github/copilot-language-server on npm](https://www.npmjs.com/package/@github/copilot-language-server)
   - [Copilot Language Server SDK announcement](https://github.blog/changelog/2025-02-10-copilot-language-server-sdk-is-now-available/)

4. **OpenAI:**
   - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
   - [Codex changelog](https://developers.openai.com/codex/changelog/)

5. **Anthropic:**
   - [Anthropic API Documentation](https://docs.anthropic.com/)
   - [Claude 3.5 Sonnet](https://www.anthropic.com/claude/sonnet)

### Blog Posts & Articles

6. **GitHub Blog:**
   - [Which AI model should I use with GitHub Copilot?](https://github.blog/ai-and-ml/github-copilot/which-ai-model-should-i-use-with-github-copilot/)
   - [GitHub Copilot coding agent 101](https://github.blog/ai-and-ml/github-copilot/github-copilot-coding-agent-101-getting-started-with-agentic-workflows-on-github/)
   - [Copilot usage metrics dashboard and API in public preview](https://github.blog/changelog/2025-10-28-copilot-usage-metrics-dashboard-and-api-in-public-preview/)
   - [New GPT-4o Copilot code completion model](https://github.blog/changelog/2025-02-18-new-gpt-4o-copilot-code-completion-model-now-available-in-public-preview-for-copilot-in-vs-code/)

7. **Community:**
   - [How to invoke Github Copilot programmatically? (Stack Overflow)](https://stackoverflow.com/questions/76741410/how-to-invoke-github-copilot-programmatically)
   - [Copilot Internals](https://thakkarparth007.github.io/copilot-explorer/posts/copilot-internals.html)
   - [Reverse Engineering Github Copilot](https://bootk.id/posts/copilot/)
   - [I Turned GitHub Copilot Into OpenAI Compatible API Provider](https://ericc-ch.github.io/blog/reverse-engineering-copilot-api/)

8. **Analysis & Comparisons:**
   - [GitHub Copilot Pricing 2025: Complete Cost Analysis](https://skywork.ai/blog/agent/github-copilot-pricing-2025-complete-cost-analysis-roi-calculator/)
   - [Claude Code vs GitHub Copilot: Complete Comparison Guide](https://skywork.ai/blog/claude-code-vs-github-copilot-2025-comparison/)
   - [OpenAI Codex: From 2021 Code Model to a 2025 Autonomous Coding Agent](https://medium.com/@aliazimidarmian/openai-codex-from-2021-code-model-to-a-2025-autonomous-coding-agent-85ef0c48730a)

### Unofficial Projects (Use at Own Risk)

9. **Reverse-Engineered Proxies:**
   - [copilot-api by ericc-ch](https://github.com/ericc-ch/copilot-api) ⚠️
   - [gh_copilot_chat by rabilrbl](https://github.com/rabilrbl/gh_copilot_chat) ⚠️
   - [copilot-explorer by thakkarparth007](https://github.com/thakkarparth007/copilot-explorer) ⚠️

10. **Editor Plugins (LSP-based):**
    - [copilot.lua for Neovim](https://github.com/zbirenbaum/copilot.lua)
    - [copilot.el for Emacs](https://github.com/copilot-emacs/copilot.el)
    - [copilot-lsp for Neovim](https://github.com/copilotlsp-nvim/copilot-lsp)

---

## Appendix A: Key Takeaways

### What GitHub Copilot IS

✅ IDE-integrated coding assistant
✅ Chat interface for code questions
✅ CLI tool for terminal assistance
✅ Code review automation
✅ PR summary generation
✅ Multi-model support (GPT-4, Claude)

### What GitHub Copilot is NOT

❌ A public API for code generation
❌ Suitable for programmatic automation at scale
❌ Designed for parallel execution
❌ A replacement for Claude/OpenAI APIs
❌ Safe to reverse engineer for production use

### For ob1 Project

✅ **Use:** Claude API (primary) + OpenAI API (secondary)
✅ **Benefit:** Official, reliable, ToS-compliant
❌ **Avoid:** GitHub Copilot unofficial proxies
❌ **Reason:** Account suspension risk, unreliable
⚠️ **Maybe:** Copilot CLI for user-supervised tasks (not parallel automation)

### Cost Comparison (100 PRs)

- **Claude 3.5 Sonnet:** ~$10-15
- **GPT-4o:** ~$12-20
- **Copilot Pro:** $10/month (300 premium requests, may not suffice)
- **Copilot Enterprise:** $39/month/user (1,000 premium requests)

### Risk Assessment

| Method | Risk Level | Recommendation |
|--------|------------|----------------|
| **Claude API** | None | ✅ Recommended |
| **OpenAI API** | None | ✅ Recommended |
| **Copilot CLI (manual)** | Low | ⚠️ Limited use only |
| **Copilot Proxy (unofficial)** | High | ❌ Avoid |

---

## Appendix B: Quick Start Templates

### Template 1: Claude Agent for ob1

```python
import asyncio
from anthropic import AsyncAnthropic
from typing import Dict, Optional

class ClaudeCodeAgent:
    """Claude-powered code generation agent for ob1."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate_pr(
        self,
        issue: str,
        repo_context: str,
        base_branch: str = "main"
    ) -> Dict[str, str]:
        """Generate code changes for a PR."""

        prompt = f"""You are a senior software engineer. Generate code changes for this issue.

Issue: {issue}

Repository Context:
{repo_context}

Provide:
1. File changes (path and content)
2. Commit message
3. PR description

Format as JSON:
{{
  "files": [{{"path": "...", "content": "..."}}],
  "commit_message": "...",
  "pr_description": "..."
}}
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_response(response.content[0].text)

    def _parse_response(self, text: str) -> Dict[str, str]:
        import json
        # Extract JSON from response
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])

# Usage
async def main():
    agent = ClaudeCodeAgent(api_key="sk-ant-...")

    result = await agent.generate_pr(
        issue="Add user authentication",
        repo_context="Python FastAPI project..."
    )

    print(f"Files to change: {len(result['files'])}")
    print(f"Commit: {result['commit_message']}")

asyncio.run(main())
```

### Template 2: OpenAI Agent for ob1

```python
from openai import AsyncOpenAI
from typing import Dict, List

class GPT4Agent:
    """GPT-4o powered code generation agent for ob1."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate_pr(
        self,
        issue: str,
        repo_context: str
    ) -> Dict[str, str]:
        """Generate code changes for a PR."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a senior software engineer."},
                {"role": "user", "content": f"""Generate code for: {issue}

Context: {repo_context}

Provide JSON with files, commit_message, pr_description."""}
            ],
            response_format={"type": "json_object"}
        )

        import json
        return json.loads(response.choices[0].message.content)

# Usage similar to ClaudeCodeAgent
```

### Template 3: Multi-Agent Orchestrator

```python
import asyncio
from typing import List, Protocol, Dict
from dataclasses import dataclass

class CodeAgent(Protocol):
    async def generate_pr(self, issue: str, repo_context: str) -> Dict[str, str]:
        ...

@dataclass
class PRResult:
    agent_name: str
    files: List[Dict[str, str]]
    commit_message: str
    pr_description: str
    branch_name: str

class ParallelOrchestrator:
    """Orchestrate multiple AI agents to create competing PRs."""

    def __init__(self, agents: Dict[str, CodeAgent]):
        self.agents = agents

    async def create_competing_prs(
        self,
        issue: str,
        repo_context: str
    ) -> List[PRResult]:
        """Create PRs from all agents in parallel."""

        tasks = [
            self._create_pr(name, agent, issue, repo_context)
            for name, agent in self.agents.items()
        ]

        return await asyncio.gather(*tasks)

    async def _create_pr(
        self,
        agent_name: str,
        agent: CodeAgent,
        issue: str,
        repo_context: str
    ) -> PRResult:
        """Create PR from single agent."""

        result = await agent.generate_pr(issue, repo_context)

        return PRResult(
            agent_name=agent_name,
            files=result["files"],
            commit_message=result["commit_message"],
            pr_description=result["pr_description"],
            branch_name=f"agent-{agent_name}-{issue[:20]}"
        )

# Usage
async def main():
    orchestrator = ParallelOrchestrator({
        "claude-1": ClaudeCodeAgent(api_key=ANTHROPIC_KEY),
        "claude-2": ClaudeCodeAgent(api_key=ANTHROPIC_KEY),
        "gpt4o": GPT4Agent(api_key=OPENAI_KEY),
    })

    prs = await orchestrator.create_competing_prs(
        issue="Add user authentication",
        repo_context="..."
    )

    for pr in prs:
        print(f"{pr.agent_name}: {pr.commit_message}")

asyncio.run(main())
```

---

## Appendix C: Decision Matrix

### Should I use GitHub Copilot for ob1?

```
┌─────────────────────────────────────────────────────┐
│ Need programmatic code generation API?              │
│                                                     │
│  YES ──────────────────────────────────────────────┤
│                                                     │
│  ┌─ Is official API available?                     │
│  │                                                  │
│  │  NO ─ GitHub Copilot ────> ❌ DON'T USE        │
│  │  YES ─ Claude/OpenAI ────> ✅ USE              │
│  │                                                  │
│  └─ Do you need parallel execution?                │
│                                                     │
│     YES ─ GitHub Copilot ────> ❌ DON'T USE       │
│     YES ─ Claude/OpenAI ────> ✅ USE              │
│                                                     │
│  NO ──────────────────────────────────────────────┤
│                                                     │
│  ┌─ Is this for IDE use?                           │
│  │                                                  │
│  │  YES ─────────────────────> ✅ Use Copilot     │
│  │  NO ──────────────────────> Consider Claude    │
│  │                                                  │
└─────────────────────────────────────────────────────┘

Result: For ob1, use Claude API or OpenAI API
```

---

**End of Research Report**

**Last Updated:** November 9, 2025
**Next Review:** When GitHub announces official Copilot API
