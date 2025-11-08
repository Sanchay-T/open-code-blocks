---
name: parallel-orchestration
description: Expert at orchestrating multiple AI agents in parallel. Use when user wants to run multiple agents, create competing solutions, or parallelize development tasks. Handles git worktrees, branch management, agent coordination.
---

# Parallel Orchestration Skill

You are an expert at orchestrating multiple AI agents to work on the same task in parallel, creating competing solutions and managing isolated workspaces.

## Core Capabilities

### 1. Git Worktree Management

**Creating Isolated Workspaces:**
- Use `git worktree add -b <branch> <path> <base-branch>` to create isolated workspaces
- Pattern: `.ob1/worktrees/<branch-name-sanitized>/`
- Each worktree gets its own branch derived from the base branch
- Worktrees allow multiple agents to work simultaneously without conflicts

**Worktree Lifecycle:**
```bash
# Create worktree
git worktree add -b ob1/run-123/agent-1 .ob1/worktrees/ob1-run-123-agent-1 main

# Work in worktree
cd .ob1/worktrees/ob1-run-123-agent-1
# ... agent makes changes ...

# Cleanup worktree
git worktree remove --force .ob1/worktrees/ob1-run-123-agent-1
git branch -D ob1/run-123/agent-1
```

**Best Practices:**
- Always create worktrees from a fresh base branch (e.g., `main`)
- Use timestamp-based run IDs: `YYYYMMDD-HHMMSS`
- Sanitize branch names for filesystem compatibility (replace `/` with `-`)
- Clean up worktrees even if agent fails
- Lock worktree operations to prevent race conditions

### 2. Parallel Agent Coordination

**Running Multiple Agents:**
Reference: `/Users/sanchay/Documents/open-code-blocks/src/ob1/orchestrator.py`

Pattern for spawning k agents in parallel:
```python
tasks = []
for idx in range(k):
    agent_name = f"agent-{idx + 1}"
    branch = f"ob1/{run_id}/{agent_name}"
    tasks.append(
        asyncio.create_task(
            run_single_agent(agent_name, branch, worktree_path)
        )
    )

# Process results as they complete
for coro in asyncio.as_completed(tasks):
    result = await coro
    # Handle result
```

**Agent Result Tracking:**
Track each agent's:
- Agent name (e.g., "claude-1")
- Branch name (e.g., "ob1/20250109-143022/claude-1")
- Status: "success", "failed", "dry-run"
- PR URL (if created)
- Error message (if failed)
- Transcript path (for debugging)

### 3. Context Building for Agents

**Gathering Repo Context:**
Reference: `/Users/sanchay/Documents/open-code-blocks/src/ob1/context_engine.py`

Provide each agent with:
1. **File snippets** - Up to 8 relevant files (600 chars each)
2. **Package summary** - Key scripts and dependencies
3. **Scope constraints** - What files they can modify

```python
# Gather context matching scope patterns
context = gather_repo_context(
    worktree=worktree_path,
    patterns=["frontend/**/*.tsx", "frontend/**/*.css"],
    max_files=8,
    max_chars_per_file=600
)

# Build prompt with context
prompt = build_prompt_text(
    task="Add dark mode toggle",
    scope_patterns=["frontend/**/*.tsx"],
    context=context
)
```

### 4. Change Validation

**Scope Enforcement:**
Reference: `/Users/sanchay/Documents/open-code-blocks/src/ob1/change_guard.py`

Before committing or creating PRs:
1. List all changed files: `git status --porcelain`
2. Verify each file matches allowed scope patterns
3. Reject if any files are outside scope

```python
files = list_changed_files(worktree)
if not files:
    raise ChangeGuardError("Agent did not modify any files")
ensure_changes_within_scope(files, scope_patterns)
```

### 5. Branch Management & PR Creation

**Push and PR Pattern:**
```python
# Commit all changes
run_git("add", "-A", cwd=worktree)
run_git("commit", "-m", f"feat: {agent_name} - {task}", cwd=worktree)

# Push to origin
run_git("push", "-u", "origin", f"{branch}:{branch}", cwd=repo_root)

# Create PR
pr_url = await gh_client.create_pull_request(
    repo=repo_ref,
    title=f"{agent_name}: {task[:60]}",
    head=branch,
    base=base_branch,
    body=pr_body
)
```

## Orchestration Workflows

### Workflow 1: Basic Parallel Run

**When to use:** User wants k agents to implement the same feature
**Steps:**
1. Generate unique run_id (timestamp)
2. Prepare target repository (clone or use current)
3. For each agent (1 to k):
   - Create worktree from base branch
   - Build context from scope patterns
   - Spawn agent with Task tool
   - Track progress
4. Collect results as agents complete
5. Create PRs for successful agents
6. Clean up all worktrees
7. Display summary table

### Workflow 2: Provider Rotation

**When to use:** User wants different AI providers (e.g., 3 Claude, 2 GPT-4)
**Pattern:**
```python
providers = ["claude", "gpt4", "claude", "gpt4", "claude"]
for idx in range(k):
    provider = providers[idx % len(providers)]
    agent_name = f"{provider}-{(idx // len(providers)) + 1}"
```

### Workflow 3: Dry Run Mode

**When to use:** Testing orchestration without creating PRs
**Behavior:**
- Create worktrees and gather context
- Skip agent execution
- Skip PR creation
- Still validate setup and cleanup

## Error Handling

### Common Failures

**Agent produced no changes:**
- Check if agent understood the task
- Verify scope patterns aren't too restrictive
- Review agent transcript for errors

**Changes outside scope:**
- Agent modified files it shouldn't have
- Reject the changes, don't create PR
- Report which files violated scope

**Worktree creation failed:**
- Branch might already exist
- Disk space issues
- Git lock conflicts

**PR creation failed:**
- Missing GitHub token
- Branch name conflicts
- API rate limits

### Cleanup Strategy

Always clean up worktrees, even on failure:
```python
try:
    # Run agent
    result = await run_agent(...)
finally:
    # Always cleanup
    if worktree_path:
        repo_manager.remove_worktree(branch, worktree_path)
```

## Results Presentation

### Summary Table
Display results in a Rich table:
```
┌─────────┬────────────────────────┬─────────┬─────────────────────┬───────┐
│ Agent   │ Branch                 │ Status  │ PR                  │ Error │
├─────────┼────────────────────────┼─────────┼─────────────────────┼───────┤
│ claude-1│ ob1/123/claude-1       │ success │ https://github...   │ —     │
│ claude-2│ ob1/123/claude-2       │ success │ https://github...   │ —     │
│ claude-3│ ob1/123/claude-3       │ failed  │ —                   │ No... │
└─────────┴────────────────────────┴─────────┴─────────────────────┴───────┘
```

### Console Output
- Print real-time updates as agents complete
- Color-code: green=success, red=failed, yellow=dry-run
- Include PR URLs for easy access

## Integration Points

### With Context Engine
- Use `gather_repo_context()` to build file context
- Respect scope patterns for filtering
- Provide package.json summary for frontend projects

### With Change Guard
- Validate all changes before PR creation
- Enforce scope boundaries strictly
- List changed files with `git status --porcelain`

### With GitHub API
- Authenticate with GITHUB_TOKEN
- Create PRs with descriptive titles/bodies
- Include agent metadata in PR description

### With Providers (Claude, etc.)
- Each provider needs its own configuration
- Pass allowed tools list
- Configure transcript saving for debugging

## Examples

### Example 1: Create 3 competing implementations
```bash
ob1 run -k 3 \
  --message "Add user profile page with avatar upload" \
  --scope "frontend/src/pages/**,frontend/src/components/**" \
  --base main
```

### Example 2: Dry run to test setup
```bash
ob1 run -k 2 \
  --message "Add dark mode toggle" \
  --scope "frontend/**/*.tsx" \
  --dry-run
```

### Example 3: Target external repo
```bash
ob1 run -k 5 \
  --message "Fix responsive layout on mobile" \
  --scope "frontend/src/**/*.css" \
  --target https://github.com/org/repo.git \
  --base main
```

## Key Files Reference

- `/Users/sanchay/Documents/open-code-blocks/src/ob1/orchestrator.py` - Main orchestration logic
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/repo_manager.py` - Worktree management
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/context_engine.py` - Context building
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/change_guard.py` - Scope validation
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/providers/claude.py` - Claude provider
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/github_api.py` - GitHub integration

## When to Use This Skill

Use this skill when the user asks to:
- "Run multiple agents in parallel"
- "Create competing solutions"
- "Orchestrate k agents to work on X"
- "Spawn agents to implement different approaches"
- "Create worktrees for isolated development"
- "Compare multiple AI implementations"

This skill is perfect for exploration, A/B testing implementations, and maximizing solution quality through competition.
