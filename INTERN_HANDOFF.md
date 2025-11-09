# Claude Agent SDK - Intern Handoff Document

## Overview

This document provides everything needed to implement Claude Agent SDK automation that works identically in both local development and production environments with **zero code changes**.

---

## What's Been Set Up

### Core Concept

We've created a universal automation framework where:
- **Same Python code** runs in both local and production
- **Local testing** uses Claude Code session (FREE)
- **Production** uses API key from environment variable (costs credits)
- **Full tool access** in both environments (files, bash, git, web)

### Key Insight

The Claude Agent SDK spawns the `claude` CLI subprocess, which handles authentication:
1. Checks for `CLAUDE_API_KEY` environment variable
2. If found → Uses API key
3. If not → Uses Claude Code session (if logged in)

**Result:** Same code, different auth source, identical behavior!

---

## Files Created for You

### 📘 Documentation

| File | Purpose |
|------|---------|
| **INTERN_HANDOFF.md** | This file - complete guide with all examples |
| **.github/workflows/example-claude-automation.yml** | GitHub Actions workflow template |

**Note:** All code examples are included inline in this document below.

---

## Quick Start for Intern

### Step 1: Read This Document (30 minutes)

Read through this entire document - it contains everything you need:
1. Architecture and concepts (10 min)
2. Code examples and templates (10 min)
3. Deployment and troubleshooting (10 min)

### Step 2: Install Prerequisites (5 minutes)

```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install claude-agent-sdk python-dotenv

# Login to Claude Code (for free local testing)
claude login
```

### Step 3: Create Your First Automation (10 minutes)

Create a file called `my_automation.py`:

```python
#!/usr/bin/env python3
"""My first Claude automation."""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

load_dotenv()

async def main():
    print("🤖 Starting automation...\n")

    options = ClaudeAgentOptions(
        permission_mode="acceptEdits",
        system_prompt="You are helpful.",
        cwd=str(Path.cwd()),
    )

    prompt = "Read README.md and summarize it in 2-3 sentences"

    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    print(block.text, end='', flush=True)

    print("\n\n✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python my_automation.py
```

### Step 4: Understand the Code (10 minutes)

Study the code above:
- Authentication is automatic (SDK checks for CLAUDE_API_KEY or uses session)
- `ClaudeAgentOptions` configures the SDK
- `query()` sends the prompt and returns responses
- The same code works locally AND in production

### Step 5: Build Your Own (Variable)

Use the example as a template and customize for your needs.

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│     Your Python Automation Code         │
│     (NEVER CHANGES!)                    │
└─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────┐
│     Claude Agent SDK (Python)           │
│     - Spawns 'claude' CLI subprocess    │
└─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────┐
│     'claude' CLI (Node.js)              │
│     - Checks for CLAUDE_API_KEY         │
│     - Falls back to Claude Code session │
└─────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
    ┌─────────┐         ┌──────────┐
    │  Local  │         │Production│
    │ Session │         │ API Key  │
    │ (FREE)  │         │ (PAID)   │
    └─────────┘         └──────────┘
```

---

## Authentication Flow

### Local Development

```bash
# Option 1: Use Claude Code session (FREE)
claude login  # One-time setup
python automation.py  # Just run it!

# Option 2: Use API key locally
echo "CLAUDE_API_KEY=sk-ant-..." > .env
python automation.py
```

### Production (GitHub Actions)

```yaml
# In workflow file
- name: Run automation
  env:
    CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
  run: python automation.py
```

**Important:** Add `CLAUDE_API_KEY` to GitHub repository secrets!

---

## Code Template

### Minimal Working Example

```python
#!/usr/bin/env python3
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    # Configure options
    options = ClaudeAgentOptions(
        permission_mode="acceptEdits",
        system_prompt="You are helpful.",
    )

    # Run automation
    async for msg in query(
        prompt="Your task here",
        options=options
    ):
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    print(block.text, end='', flush=True)

asyncio.run(main())
```

**This code works in both local and production with no changes!**

---

## Common Tasks

### Task 1: Code Review Automation

```python
prompt = """
Review all Python files in src/:
1. Check for common bugs
2. Identify security issues
3. Suggest improvements
Write report to review.md
"""
```

### Task 2: Test Generation

```python
prompt = """
Generate pytest tests for main.py:
1. Test all public functions
2. Include edge cases
3. Save to tests/test_main.py
"""
```

### Task 3: Documentation

```python
prompt = """
Generate API documentation:
1. Read all .py files in src/
2. Extract docstrings
3. Generate docs/API.md
"""
```

---

## Available Tools

The SDK has access to all Claude Code tools:

| Tool | What It Does | Example Use |
|------|--------------|-------------|
| **Read** | Read files | Load source code |
| **Write** | Create files | Generate new code |
| **Edit** | Modify files | Fix bugs |
| **Bash** | Run commands | `git status`, `npm test` |
| **Grep** | Search in files | Find all TODOs |
| **Glob** | Find files | `**/*.py` |
| **WebSearch** | Search web | Find docs |
| **WebFetch** | Fetch URLs | Read API docs |

---

## Cost Management

### Understanding Costs

- **Input tokens:** ~$3 per 1M tokens
- **Output tokens:** ~$15 per 1M tokens

### Example Costs

| Task | Tokens | Cost |
|------|--------|------|
| Small (100 tokens) | 100 | ~$0.002 |
| Medium (1000 tokens) | 1000 | ~$0.015 |
| Large (5000 tokens) | 5000 | ~$0.075 |

### Best Practices

1. **Always test locally first** (free with Claude Code session)
2. **Set budget limits** using `max_budget_usd` option
3. **Limit max_tokens** to reasonable values
4. **Monitor usage** at console.anthropic.com

### Budget Control Example

```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",
    max_budget_usd=0.10,  # Stop if exceeds $0.10
    max_tokens=1000,      # Limit response length
)
```

---

## Deployment Checklist

### Local Testing

- [ ] Install Claude CLI: `npm install -g @anthropic-ai/claude-code`
- [ ] Install Python SDK: `pip install claude-agent-sdk`
- [ ] Login to Claude: `claude login` OR set API key in `.env`
- [ ] Run example: `python example_automation.py`
- [ ] Verify it works

### Production Deployment

- [ ] Get API key from https://console.anthropic.com/settings/keys
- [ ] Add credits to account (minimum $5 recommended)
- [ ] Add `CLAUDE_API_KEY` to GitHub secrets
- [ ] Copy `.github/workflows/example-claude-automation.yml`
- [ ] Customize workflow for your needs
- [ ] Test with manual trigger first
- [ ] Monitor costs and results

---

## Troubleshooting Guide

### Issue: "Claude Code not found"

**Solution:**
```bash
npm install -g @anthropic-ai/claude-code
claude --version  # Verify installation
```

### Issue: "Authentication failed"

**Solution:**
```bash
# Check if API key is set
echo $CLAUDE_API_KEY

# If not, either:
export CLAUDE_API_KEY=sk-ant-...
# OR
claude login
```

### Issue: "Low credit balance"

**Solution:**
- Add credits at https://console.anthropic.com/settings/billing
- Or use Claude Code session for local testing (free)

### Issue: "Permission denied" for file operations

**Solution:**
```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",  # Auto-accept edits
)
```

---

## Security Reminders

### ⚠️ NEVER commit API keys

```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### ✅ Use environment variables

```python
import os
api_key = os.getenv("CLAUDE_API_KEY")  # Good
# api_key = "sk-ant-..."  # BAD - Never hardcode!
```

### ✅ Rotate keys regularly

Generate new keys periodically at console.anthropic.com

---

## Testing Strategy

### Phase 1: Local Testing (Free)

```bash
# Use Claude Code session - no cost
claude login
python automation.py
```

**Goal:** Verify automation logic works

### Phase 2: API Validation (Minimal Cost)

```bash
# Use API key with small test
export CLAUDE_API_KEY=sk-ant-...
python automation.py  # Run once to verify
```

**Goal:** Confirm API key works (~$0.01)

### Phase 3: Production Deploy

```yaml
# Deploy to GitHub Actions
# Monitor first few runs closely
```

**Goal:** Verify production automation

---

## Support Resources

### Documentation

- **INTERN_HANDOFF.md** - This complete guide (you're reading it!)
- **.github/workflows/example-claude-automation.yml** - GitHub Actions template

### External Links

- **Claude Console:** https://console.anthropic.com/
- **API Docs:** https://docs.anthropic.com/
- **Pricing:** https://www.anthropic.com/pricing

### Getting Help

1. Check the Troubleshooting section in this document
2. Review the code examples above
3. Test locally to isolate issues
4. Check API key and credits at console.anthropic.com

---

## Success Criteria

Your intern should be able to:

- [ ] Explain how SDK authentication works
- [ ] Install and configure local environment
- [ ] Create and run their first automation
- [ ] Understand code structure
- [ ] Build a simple custom automation
- [ ] Deploy to GitHub Actions
- [ ] Monitor costs and results

---

## Next Steps for Intern

1. **Day 1:** Read this doc, install tools, create first automation
2. **Day 2:** Study code structure, understand SDK options
3. **Day 3:** Build first custom automation (locally)
4. **Day 4:** Test with API key, deploy to GitHub Actions
5. **Day 5:** Refine and optimize

---

## Key Takeaways

### For the Intern

✅ **Same code works everywhere** - local and production
✅ **Free local testing** - use Claude Code session
✅ **Full tool access** - files, bash, git, web
✅ **Simple deployment** - just set environment variable
✅ **Cost effective** - typical tasks cost $0.01-0.10

### For the Team

✅ **Rapid prototyping** - test locally for free
✅ **Production ready** - deploy with API key
✅ **Predictable costs** - set budget limits
✅ **Maintainable** - same code, clear docs
✅ **Scalable** - CI/CD integration ready

---

## Questions to Ask Your Intern

After they've gone through the docs:

1. How does the SDK authenticate in local vs production?
2. What tools does the SDK have access to?
3. How do you set a budget limit?
4. Where would you add the API key in GitHub Actions?
5. What's the cost of a typical automation task?

**Expected answers are all in this document - scroll up to find them!**

---

## Final Notes

- All trial/test files have been cleaned up
- All code examples are embedded in this document
- Code has been tested and verified working
- GitHub Actions template is ready at `.github/workflows/example-claude-automation.yml`
- API key authentication confirmed working
- This is the ONLY document your intern needs to read

**Everything is ready for your intern to start!** 🚀

---

**Created:** 2025-01-09
**Version:** 1.0
**Status:** Production Ready
