# ob1 - Parallel AI SWE Agent Orchestrator

**Run multiple AI agents in parallel on the same task, creating competing pull requests.**

## 🎯 What is ob1?

`ob1` orchestrates k AI software engineering agents to work on the same task simultaneously. Each agent:
- Gets its own isolated git worktree
- Makes code changes autonomously using Claude
- Creates a pull request with its solution

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .
```

### Setup

```bash
export GITHUB_TOKEN="ghp_your_token"
export ANTHROPIC_API_KEY="sk-ant-your_key"
```

### Usage

```bash
ob1 -m "Build a React login component" -k 3
```

## 📝 Stage 1 Complete ✅

- ✅ Parallel AI agent orchestration
- ✅ Git worktree isolation
- ✅ Automatic PR creation
- ✅ Extensible architecture (easy to add Codex/Cursor)
- ✅ Clean, modular codebase (<300 lines per file)

---

**Built for the OpenBlock coding challenge**
