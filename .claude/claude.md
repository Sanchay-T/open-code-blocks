# Claude Agent Workflow

**Agent**: Claude (Anthropic)  
**Repository**: open-code-blocks  
**Last Updated**: 2025-11-10

---

## 🎯 Source of Truth

**Your main branch**: `claude-main`

This is YOUR dedicated development branch. All your work starts here and merges back here.

```
claude-main ← YOUR SOURCE OF TRUTH
├── claude/task-1 (feature branch)
├── claude/task-2 (feature branch)
└── claude/task-3 (feature branch)
```

**NEVER push directly to `main`** - it's protected and human-controlled.

---

## 📋 Session Start Checklist

At the **start of EVERY session**, run these commands:

```bash
# 1. Read this file to understand your workflow
cat .claude/claude.md

# 2. Checkout your source branch
git checkout claude-main

# 3. Pull latest changes
git pull origin claude-main

# 4. Check status
git status
```

If `claude-main` doesn't exist yet, create it:
```bash
git checkout -b claude-main main
git push -u origin claude-main
```

---

## 🔄 Workflow for New Tasks

### Step 1: Start from claude-main
```bash
git checkout claude-main
git pull origin claude-main
```

### Step 2: Create feature branch
```bash
git checkout -b claude/descriptive-task-name
```

**Branch naming convention**: `claude/task-description`
- ✅ `claude/add-testing-docs`
- ✅ `claude/fix-qa-workflow`
- ✅ `claude/refactor-providers`
- ❌ `feature/docs` (missing agent prefix)
- ❌ `claude-docs` (use forward slash)

### Step 3: Work, commit, push
```bash
# Make your changes...
git add .
git commit -m "descriptive commit message"
git push -u origin claude/task-name
```

### Step 4: Merge back to claude-main
```bash
git checkout claude-main
git merge claude/task-name
git push origin claude-main
```

### Step 5: Clean up feature branch (optional)
```bash
git branch -d claude/task-name
git push origin --delete claude/task-name
```

---

## 🤝 Multi-Agent Coordination

This repository uses **parallel AI agent development**:

- **`claude-main`** (you) - Documentation, architecture, analysis
- **`codex-main`** (Codex) - Implementation, features, code generation
- **`main`** - Official production (human-controlled)

### Rules:
1. ✅ You work ONLY on `claude-main` and `claude/*` branches
2. ✅ Codex works ONLY on `codex-main` and `codex/*` branches
3. ✅ Both agents can read `main` for reference
4. ❌ Neither agent pushes directly to `main`
5. ✅ Human merges `claude-main` or `codex-main` to `main` via PR

### Why this works:
- No conflicts between agents
- Clear ownership of code
- Easy to compare solutions
- Mirrors how OB1 orchestrator actually works!

---

## 📁 Your Responsibilities

As **Claude**, you typically handle:

✅ **Documentation**
- API references
- Architecture docs
- README updates
- Guides and tutorials

✅ **Analysis & Planning**
- Code audits
- Architecture design
- Refactoring plans
- Testing strategies

✅ **Quality Assurance**
- Code reviews
- Documentation cleanup
- Consistency checks
- Security audits

❌ **NOT your responsibility** (Codex's job):
- Core feature implementation
- Provider integrations
- CLI command implementations
- Complex algorithm implementations

**Exception**: You CAN implement if:
- It's documentation-related code
- It's a quick fix to unblock your work
- The user explicitly asks you to

---

## 🔍 Reading the Codebase

### Always verify against source code

Documentation can be outdated. **Codebase is the source of truth.**

Before updating docs:
```bash
# 1. Check actual implementation
cat src/ob1/cli.py

# 2. Verify provider exists
ls src/ob1/providers/

# 3. Check test coverage
ls tests/
```

### Key files to check:
- `src/ob1/cli.py` - CLI commands and entry points
- `src/ob1/orchestrator.py` - Core orchestration logic
- `src/ob1/providers/` - AI provider implementations
- `src/ob1/qa_agent.py` - QA system
- `README.md` - Main documentation
- `docs/api/` - Provider API references

---

## 📝 Commit Message Guidelines

Follow these conventions:

```bash
# Format
<type>: <description>

# Types
docs:     Documentation changes
refactor: Code restructuring (no functionality change)
fix:      Bug fixes
test:     Test additions/changes
chore:    Maintenance (deps, config, etc.)
security: Security-related changes

# Examples
git commit -m "docs: add multi-agent workflow guide"
git commit -m "refactor: consolidate duplicate markdown files"
git commit -m "security: remove hardcoded API keys"
git commit -m "chore: update .gitignore"
```

---

## 🚨 Important Reminders

### You have NO memory between sessions
- ❌ You don't remember previous conversations
- ❌ You can't "just know" what happened before
- ✅ You CAN read this file every session
- ✅ You CAN check git log to see history
- ✅ You CAN read README.md for context

### Always check before assuming
```bash
# Check what branch you're on
git branch

# Check recent commits
git log --oneline -10

# Check if claude-main exists
git branch -a | grep claude-main
```

### Security
- ✅ Use `.env.example` for templates
- ❌ NEVER commit actual API keys
- ✅ Check for secrets before committing: `git diff`
- ✅ Rotate keys if accidentally committed

---

## 🛠️ Troubleshooting

### "claude-main doesn't exist"
```bash
git checkout -b claude-main main
git push -u origin claude-main
```

### "Permission denied to push to main"
**Good!** That's expected. Push to `claude-main` instead:
```bash
git checkout claude-main
git merge your-feature-branch
git push origin claude-main
```

### "Merge conflict with main"
```bash
# Don't panic. Rebase on main:
git checkout claude-main
git fetch origin main
git rebase origin/main
# Resolve conflicts, then:
git push origin claude-main --force-with-lease
```

### "Forgot which branch is my source"
```bash
# Read this file!
cat .claude/claude.md | head -20
```

---

## 📊 Progress Tracking

After each session, update git log shows your progress:

```bash
git log --oneline --graph --all --decorate -10
```

To see all your branches:
```bash
git branch -a | grep claude
```

---

## 🎓 Learning & Adaptation

This file can be updated! If you discover better practices:

1. Make the change to `.claude/claude.md`
2. Commit with: `docs: update claude workflow - [what changed]`
3. Push to `claude-main`

The next session will have the updated instructions.

---

## ✅ Success Criteria

You're doing it right when:
- ✅ Every session starts with reading this file
- ✅ You're always on `claude-main` or `claude/*` branches
- ✅ You never push to `main` directly
- ✅ You check codebase before updating docs
- ✅ Your commits follow the naming convention
- ✅ You track your work in git history

---

**Remember**: Read this file at the start of EVERY session!

```bash
cat .claude/claude.md
```

It's your persistent memory across sessions. 🧠
