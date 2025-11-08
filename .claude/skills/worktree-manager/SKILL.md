# Worktree Manager Skill

## Overview

Expert at git worktree management for parallel development workflows. This skill provides comprehensive worktree lifecycle management, enabling isolated workspaces for concurrent feature development without conflicts.

## When to Use This Skill

Invoke this skill when you need to:
- Create isolated git worktrees for parallel development
- Manage multiple feature branches simultaneously
- Set up workspace for AI agent orchestration
- Clean up and remove worktrees safely
- Handle worktree conflicts and errors
- Validate worktree state and integrity

## Core Capabilities

### 1. Worktree Creation

Create isolated worktrees with proper naming conventions and branching strategies.

**Branch Naming Conventions:**
- Feature branches: `feat-{description}` or `feat/{description}`
- Bug fixes: `fix-{description}` or `fix/{description}`
- Hotfixes: `hotfix-{description}` or `hotfix/{description}`
- Experimental: `exp-{description}` or `exp/{description}`

**Safety Checks Before Creation:**
```bash
# Verify repository is valid
git rev-parse --is-inside-work-tree

# Check if branch already exists
git branch --list {branch-name}

# Verify base branch exists
git rev-parse --verify {base-branch}

# Ensure no uncommitted changes in main repo
git status --porcelain
```

**Creation Workflow:**
```bash
# 1. Fetch latest changes from origin
git fetch origin {base-branch}

# 2. Create worktree with new branch
git worktree add -b {branch-name} {path} origin/{base-branch}

# 3. Verify creation
cd {path} && git branch --show-current

# 4. Confirm worktree is listed
git worktree list
```

**Recommended Paths:**
- Relative: `./worktrees/{branch-name}`
- Absolute: `/tmp/ob1-worktrees/{agent-id}`

### 2. Worktree Inspection

Monitor and validate worktree state.

**List All Worktrees:**
```bash
# Porcelain format for parsing
git worktree list --porcelain

# Human-readable format
git worktree list
```

**Check Worktree Status:**
```bash
# From within worktree
git status
git log --oneline -5
git diff origin/{base-branch}...HEAD

# Check for uncommitted changes
git diff-index --quiet HEAD -- || echo "Has uncommitted changes"
```

**Validate Worktree Health:**
```bash
# Verify worktree is properly linked
git worktree list | grep {path}

# Check if worktree branch exists
git branch --list {branch-name}

# Ensure no lock files blocking operations
ls -la .git/worktrees/{branch-name}/
```

### 3. Worktree Management

Handle the full lifecycle of worktrees.

**Move Worktree:**
```bash
# Move to new location
git worktree move {old-path} {new-path}
```

**Lock/Unlock Worktree:**
```bash
# Lock to prevent auto-pruning (useful for external drives)
git worktree lock {path} --reason "Agent still working"

# Unlock when ready
git worktree unlock {path}
```

**Repair Broken Worktrees:**
```bash
# If worktree was manually moved/deleted
git worktree repair {path}

# Or repair from main repo
git worktree repair
```

### 4. Cleanup and Removal

Safely remove worktrees and clean up resources.

**Safe Removal Workflow:**
```bash
# 1. Navigate out of worktree
cd {main-repo-path}

# 2. Check for uncommitted changes
git -C {worktree-path} status --porcelain

# 3. Remove worktree (will fail if uncommitted changes exist)
git worktree remove {path}

# 4. Force remove if needed (dangerous!)
git worktree remove {path} --force

# 5. Optionally delete the branch
git branch -D {branch-name}
```

**Prune Stale References:**
```bash
# Remove references to deleted worktrees
git worktree prune

# Dry run to see what would be pruned
git worktree prune --dry-run
```

**Bulk Cleanup:**
```bash
# Remove all worktrees in a directory
for wt in worktrees/*; do
  git worktree remove "$wt" --force
done

# Prune after bulk removal
git worktree prune
```

### 5. Conflict Resolution

Handle common worktree issues and errors.

**Common Errors and Solutions:**

**Error: "fatal: '{path}' already exists"**
```bash
# Solution: Remove existing directory first
rm -rf {path}
git worktree add -b {branch-name} {path} {base-ref}
```

**Error: "fatal: '{branch}' is already checked out"**
```bash
# Solution 1: Use different branch name
git worktree add -b {branch-name}-alt {path} {base-ref}

# Solution 2: Remove existing worktree first
git worktree remove {existing-path}
```

**Error: "fatal: invalid reference: {base-ref}"**
```bash
# Solution: Fetch from origin first
git fetch origin {base-ref}
git worktree add -b {branch-name} {path} origin/{base-ref}
```

**Error: "Worktree directory not empty"**
```bash
# Solution: Force remove and recreate
git worktree remove {path} --force
rm -rf {path}
git worktree add -b {branch-name} {path} {base-ref}
```

## Integration with ob1 Codebase

### Using WorktreeManager Class

Reference: `/ob1/workspace/worktree.py`

```python
from ob1.workspace.worktree import WorktreeManager

# Initialize manager
manager = WorktreeManager(
    repo_path="/path/to/repo",
    base_branch="main"
)

# Create worktree for agent
worktree_path = manager.create(
    agent_id="agent-1",
    branch_name="feat-new-feature"
)

# List all worktrees
worktrees = manager.list_worktrees()
for wt in worktrees:
    print(f"{wt['branch']}: {wt['path']}")

# Cleanup when done
manager.cleanup(worktree_path)

# Or cleanup all ob1 worktrees
manager.cleanup_all()
```

### Using git_ops Module

Reference: `/src/ob1/git_ops.py`

```python
from ob1.git_ops import add_worktree, run_git, GitError
from pathlib import Path

# Create worktree
try:
    add_worktree(
        path=Path("./worktrees/feat-login"),
        branch="feat-login",
        base_ref="main",
        cwd=Path.cwd()
    )
except GitError as e:
    print(f"Failed: {e}")
```

### CLI Integration

Reference: `/src/ob1/cli.py`

```bash
# Create worktree via CLI
ob1 mkworktree feat-login --base=main --path=./worktrees/feat-login

# Check repository health
ob1 doctor
```

## Best Practices

### 1. Naming Conventions

**DO:**
- Use descriptive branch names: `feat-user-authentication`
- Include issue/ticket numbers: `feat-123-add-login`
- Use consistent prefixes: `feat-`, `fix-`, `hotfix-`, `exp-`

**DON'T:**
- Use spaces in branch names
- Use special characters beyond `-`, `_`, `/`
- Create excessively long names (>50 chars)

### 2. Path Management

**DO:**
- Keep worktrees in dedicated directory: `./worktrees/`
- Use branch name in path: `./worktrees/feat-login/`
- Use absolute paths for programmatic access
- Add worktrees directory to `.gitignore`

**DON'T:**
- Create worktrees inside each other
- Use paths with spaces without quoting
- Create worktrees outside project scope without clear reason

### 3. Lifecycle Management

**DO:**
- Fetch latest changes before creating worktree
- Clean up worktrees after PR is merged
- Run `git worktree prune` periodically
- Check for uncommitted changes before removal

**DON'T:**
- Leave stale worktrees indefinitely
- Manually delete worktree directories (use `git worktree remove`)
- Force remove without checking for unsaved work
- Create worktrees from dirty working tree

### 4. Parallel Development

**DO:**
- Create separate worktree for each parallel task
- Use unique branch names for each agent/worker
- Coordinate base branch updates across worktrees
- Test in worktree before pushing

**DON'T:**
- Share worktrees between multiple processes
- Modify same files across multiple worktrees simultaneously
- Create circular dependencies between worktrees
- Assume worktrees auto-sync with main repo

### 5. Safety and Validation

**DO:**
- Always verify repository state before operations
- Use `--dry-run` flags when available
- Backup important uncommitted work
- Log worktree operations for debugging
- Handle errors gracefully with proper cleanup

**DON'T:**
- Use `--force` flags without understanding implications
- Ignore error messages from git
- Skip validation checks for automation speed
- Remove worktrees with uncommitted critical changes

## Automation Examples

### Create Worktree for AI Agent

```bash
#!/bin/bash
# create_agent_worktree.sh

AGENT_ID=$1
TASK_DESC=$2
BASE_BRANCH=${3:-main}

# Validate inputs
if [[ -z "$AGENT_ID" ]] || [[ -z "$TASK_DESC" ]]; then
    echo "Usage: $0 <agent-id> <task-description> [base-branch]"
    exit 1
fi

# Generate branch name
BRANCH_NAME="feat-$(echo $TASK_DESC | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
WORKTREE_PATH="./worktrees/${BRANCH_NAME}"

# Safety checks
if [[ -d "$WORKTREE_PATH" ]]; then
    echo "Error: Worktree already exists at $WORKTREE_PATH"
    exit 1
fi

# Fetch latest
git fetch origin $BASE_BRANCH

# Create worktree
git worktree add -b $BRANCH_NAME $WORKTREE_PATH origin/$BASE_BRANCH

# Configure worktree
cd $WORKTREE_PATH
git config user.name "OB1 Agent $AGENT_ID"
git config user.email "agent-${AGENT_ID}@ob1.local"

echo "Created worktree for $AGENT_ID at $WORKTREE_PATH"
echo "Branch: $BRANCH_NAME"
```

### Cleanup Merged Worktrees

```bash
#!/bin/bash
# cleanup_merged_worktrees.sh

BASE_BRANCH=${1:-main}

# Get list of merged branches
MERGED_BRANCHES=$(git branch --merged $BASE_BRANCH | grep -v "^\*" | grep -E "feat-|fix-")

for BRANCH in $MERGED_BRANCHES; do
    # Find worktree for this branch
    WORKTREE=$(git worktree list --porcelain | grep -A2 "branch refs/heads/$BRANCH" | grep "worktree" | awk '{print $2}')

    if [[ -n "$WORKTREE" ]]; then
        echo "Removing worktree: $WORKTREE (branch: $BRANCH)"
        git worktree remove $WORKTREE
        git branch -d $BRANCH
    fi
done

# Prune stale references
git worktree prune
```

## Troubleshooting Guide

### Issue: Worktree creation fails with "already exists"

**Diagnosis:**
```bash
git worktree list | grep {path}
ls -ld {path}
```

**Solution:**
```bash
# If listed but directory doesn't exist
git worktree prune

# If directory exists
git worktree remove {path} --force
rm -rf {path}
```

### Issue: Cannot remove worktree due to uncommitted changes

**Diagnosis:**
```bash
git -C {path} status --porcelain
```

**Solution:**
```bash
# Option 1: Commit changes
cd {path}
git add -A
git commit -m "WIP: Save work before cleanup"

# Option 2: Stash changes
git stash push -m "Saved work from worktree"

# Option 3: Force remove (loses changes!)
git worktree remove {path} --force
```

### Issue: Worktree shows wrong branch

**Diagnosis:**
```bash
cd {path}
git branch --show-current
git status
```

**Solution:**
```bash
# Checkout correct branch
git checkout {expected-branch}

# Or repair worktree
git worktree repair
```

### Issue: Performance degradation with many worktrees

**Diagnosis:**
```bash
git worktree list | wc -l
du -sh .git/worktrees/
```

**Solution:**
```bash
# Remove unused worktrees
git worktree prune

# Archive old branches
git branch -a | grep "feat-" | xargs -n1 git branch -D

# Clean up git database
git gc --aggressive
```

## Quick Reference

### Essential Commands

```bash
# Create worktree
git worktree add -b {branch} {path} {base-ref}

# List worktrees
git worktree list [--porcelain]

# Remove worktree
git worktree remove {path} [--force]

# Prune stale worktrees
git worktree prune [--dry-run]

# Move worktree
git worktree move {old-path} {new-path}

# Lock/unlock worktree
git worktree lock {path} --reason "..."
git worktree unlock {path}

# Repair broken worktree
git worktree repair [{path}]
```

### Useful Aliases

Add to `.gitconfig`:

```ini
[alias]
    wt = worktree
    wta = worktree add
    wtl = worktree list
    wtr = worktree remove
    wtp = worktree prune
    wtm = worktree move
```

## Environment Considerations

### Disk Space

- Each worktree shares `.git` objects (efficient)
- Worktrees primarily use space for working tree files
- Monitor with: `du -sh worktrees/*`

### Performance

- Worktrees are fast for switching contexts (no checkout needed)
- Parallel git operations possible across worktrees
- Shared object database prevents duplication

### Limitations

- Cannot check out same branch in multiple worktrees
- Some git operations may lock shared resources
- External tools may not recognize worktree structure

## Integration with ob1 Orchestrator

When orchestrating multiple AI agents:

1. **Isolation**: Each agent gets dedicated worktree
2. **Parallelism**: Agents work simultaneously without conflicts
3. **Safety**: Changes isolated until PR creation
4. **Cleanup**: Automatic removal after PR merge/close

**Example Orchestration Flow:**

```python
from ob1.workspace.worktree import WorktreeManager

manager = WorktreeManager(repo_path=".", base_branch="main")

# Create worktrees for k agents
worktrees = []
for i in range(k):
    agent_id = f"agent-{i+1}"
    branch = f"feat-task-{i+1}"
    path = manager.create(agent_id, branch)
    worktrees.append({"agent": agent_id, "path": path, "branch": branch})

# Agents work in parallel...

# Cleanup after PRs created
for wt in worktrees:
    manager.cleanup(wt["path"])
```

## Additional Resources

- Git Worktree Documentation: https://git-scm.com/docs/git-worktree
- ob1 Worktree Module: `/ob1/workspace/worktree.py`
- ob1 Git Operations: `/src/ob1/git_ops.py`
- ob1 CLI Commands: `/src/ob1/cli.py`

---

**Remember:** Always validate repository state before worktree operations and clean up resources when done. Worktrees are powerful but require disciplined lifecycle management.
