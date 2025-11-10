# Codex Agent Workflow

**Agent**: Codex (OpenAI)  
**Repository**: open-code-blocks  
**Last Updated**: 2025-11-10

---

## 🎯 Source of Truth

**Your main branch**: `codex-main`

This is YOUR dedicated development branch. All your work starts here and merges back here.

```
codex-main ← YOUR SOURCE OF TRUTH
├── codex/task-1 (feature branch)
├── codex/task-2 (feature branch)
└── codex/task-3 (feature branch)
```

**NEVER push directly to `main`** - it's protected and human-controlled.

---

## 📋 Session Start Checklist

At the **start of EVERY session**, run these commands:

```bash
# 1. Read this file to understand your workflow
cat .codex/codex.md

# 2. Checkout your source branch
git checkout codex-main

# 3. Pull latest changes
git pull origin codex-main

# 4. Check status
git status
```

If `codex-main` doesn't exist yet, create it:
```bash
git checkout -b codex-main main
git push -u origin codex-main
```

---

## 🔄 Workflow for New Tasks

### Step 1: Start from codex-main
```bash
git checkout codex-main
git pull origin codex-main
```

### Step 2: Create feature branch
```bash
git checkout -b codex/descriptive-task-name
```

**Branch naming convention**: `codex/task-description`
- ✅ `codex/implement-cursor-provider`
- ✅ `codex/add-qa-system`
- ✅ `codex/fix-orchestrator-bug`
- ❌ `feature/provider` (missing agent prefix)
- ❌ `codex-provider` (use forward slash)

### Step 3: Work, commit, push
```bash
# Make your changes...
git add .
git commit -m "descriptive commit message"
git push -u origin codex/task-name
```

### Step 4: Merge back to codex-main
```bash
git checkout codex-main
git merge codex/task-name
git push origin codex-main
```

---

## 🤝 Multi-Agent Coordination

This repository uses **parallel AI agent development**:

- **`codex-main`** (you) - Implementation, features, core functionality
- **`claude-main`** (Claude) - Documentation, architecture, analysis
- **`main`** - Official production (human-controlled)

### Rules:
1. ✅ You work ONLY on `codex-main` and `codex/*` branches
2. ✅ Claude works ONLY on `claude-main` and `claude/*` branches
3. ✅ Both agents can read `main` for reference
4. ❌ Neither agent pushes directly to `main`
5. ✅ Human merges `codex-main` or `claude-main` to `main` via PR

---

## 📁 Your Responsibilities

As **Codex**, you typically handle:

✅ **Implementation**
- Provider implementations (Claude, Cursor, Codex)
- CLI commands and features
- Orchestrator logic
- QA system implementation

✅ **Core Features**
- Algorithm implementations
- API integrations
- Git operations
- Parallel execution logic

✅ **Bug Fixes**
- Fix broken providers
- Resolve runtime errors
- Performance optimizations

❌ **NOT your responsibility** (Claude's job):
- Documentation writing
- Architecture planning
- Code audits
- Markdown file management

**Exception**: You CAN write docs if:
- It's inline code comments
- It's docstrings for your functions
- The user explicitly asks you to

---

## 📝 Commit Message Guidelines

```bash
# Format
<type>: <description>

# Types
feat:     New features
fix:      Bug fixes
perf:     Performance improvements
refactor: Code restructuring
test:     Test changes
chore:    Dependencies, config, etc.

# Examples
git commit -m "feat: implement Cursor provider"
git commit -m "fix: resolve orchestrator race condition"
git commit -m "perf: optimize context gathering"
```

---

## 🚨 Important Reminders

- You have NO memory between sessions - read this file every time!
- Always check `git branch` to see where you are
- Never push directly to `main` (it's protected)
- Check `.codex/codex.md` at the start of every session

---

**Remember**: Read this file at the start of EVERY session!

```bash
cat .codex/codex.md
```
