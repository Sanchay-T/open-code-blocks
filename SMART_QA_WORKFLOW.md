# Smart QA Agent with Memory & Developer Handoff

## Overview

The Smart QA Agent is a truly autonomous system that:
1. **Detects blockers** before attempting to test
2. **Comments on PRs** with actionable fix instructions
3. **Remembers previous issues** and checks if they're fixed
4. **Generates developer handoffs** in a format agents can parse
5. **Resumes testing** once blockers are resolved

## Workflow

### Scenario 1: First QA Run (Blocker Detected)

```
PR #28 opened by developer
├─> QA Agent triggered
├─> Loads state: No previous attempts
├─> analyze_integration("Dashboard", "Charts", "Sidebar")
│   └─> ❌ Blocker detected: No routing configured
├─> report_blocker
│   ├─> Posts comment on PR #28
│   ├─> Generates developer_handoff_pr28.md
│   └─> Saves state: BLOCKED (missing_routing)
└─> Status: BLOCKED - waiting for fix
```

**PR Comment Posted:**
```markdown
## 🚫 QA Blocker Detected

**PR:** #28
**Repository:** Sanchay-T/ob1-sandbox
**Blocker Type:** `missing_routing`

### Issue Description
Components were added but not integrated into App.jsx.
- Dashboard.jsx exists but is not imported
- No BrowserRouter/Routes configured
- Cannot test features that don't render

### Files to Modify
- `frontend/src/App.jsx`
- `frontend/src/main.jsx` (if needed for router)

### Fix Instructions
1. Add routing configuration:
   ```jsx
   import { BrowserRouter, Routes, Route } from 'react-router-dom'
   import Dashboard from './components/Dashboard'

   function App() {
     return (
       <BrowserRouter>
         <Routes>
           <Route path="/" element={<LoginForm />} />
           <Route path="/dashboard" element={<Dashboard />} />
         </Routes>
       </BrowserRouter>
     )
   }
   ```
2. Install react-router-dom if not present
3. Wire up Dashboard components properly

### For Developer Agent
```json
{
  "action": "fix_blocker",
  "pr_number": 28,
  "repository": "Sanchay-T/ob1-sandbox",
  "blocker_type": "missing_routing",
  "files_to_modify": ["frontend/src/App.jsx"],
  "instructions": "Add BrowserRouter and Routes..."
}
```
```

### Scenario 2: Developer Fixes Issue & Pushes

```
Developer Agent (or human):
├─> Reads developer_handoff_pr28.md
├─> Parses JSON instructions
├─> Modifies App.jsx to add routing
├─> Pushes to PR #28
└─> PR updated ✓
```

### Scenario 3: QA Runs Again (Blocker Resolved)

```
PR #28 updated
├─> QA Agent triggered again
├─> Loads state: Previous attempt BLOCKED (missing_routing)
├─> get_pr_info
│   └─> is_retry: true
│   └─> previous_blockers: ["missing_routing"]
├─> analyze_integration("Dashboard", "Charts", "Sidebar")
│   └─> ✓ Routing exists!
│   └─> ✓ Components imported!
│   └─> Status: INTEGRATED
├─> run_qa_tests(strategy="test_at_route")
│   ├─> Generate Playwright tests for /dashboard
│   ├─> Run tests with video recording
│   └─> ✓ Tests PASSED
├─> finish_qa
│   └─> Status: PASSED
└─> Posts success comment on PR
```

## State Management

**State file: `.qa_state_pr_28.json`**
```json
{
  "pr_number": 28,
  "attempts": [
    {
      "timestamp": "2025-01-09T15:00:00",
      "status": "BLOCKED",
      "blocker": "missing_routing"
    },
    {
      "timestamp": "2025-01-09T16:30:00",
      "status": "PASSED",
      "summary": "All tests passed after routing was fixed"
    }
  ],
  "known_issues": ["missing_routing"],
  "last_status": "PASSED"
}
```

## Developer Handoff Format

**File: `developer_handoff_pr28.md`**

Contains:
1. **Human-readable** markdown report
2. **Machine-parseable** JSON block for agents
3. **Repo/PR context** (which repo, which PR)
4. **Exact files** to modify
5. **Step-by-step** fix instructions

## Integration with OB1

### Full Dev-QA Loop

```
1. OB1 Developer Agent creates PR
   └─> Adds components but forgets routing

2. QA Agent detects blocker
   └─> Posts to PR: "Missing routing"
   └─> Generates developer_handoff_pr28.md

3. OB1 sees QA blocker
   └─> Reads handoff file
   └─> Creates fix PR or pushes to same PR

4. QA Agent sees update
   └─> Remembers "last time routing was broken"
   └─> Checks if fixed
   └─> Routing fixed! ✓
   └─> Runs tests
   └─> Success!

5. PR approved & merged
```

## Key Features

### 1. Blocker Detection

```python
# analyze_integration checks:
- ✓ Are new components imported?
- ✓ Is routing configured?
- ✓ Are routes defined?
- ✓ Can users access new features?

# If NO → BLOCKER → Report, don't test
```

### 2. Memory

```python
# On retry:
if is_retry:
    check_if_previous_blockers_fixed()
    if fixed:
        continue_with_testing()
    else:
        report_still_blocked()
```

### 3. Developer Handoff

```python
# Structured format:
{
  "action": "fix_blocker",
  "repository": "owner/repo",  # Which repo
  "pr_number": 28,              # Which PR
  "blocker_type": "missing_routing",
  "files_to_modify": ["App.jsx"],
  "instructions": "exact steps..."
}
```

## Usage

```python
from ob1.smart_qa_agent import run_smart_qa

# First run
report = await run_smart_qa(
    pr_number=28,
    repo_url="https://github.com/Sanchay-T/ob1-sandbox.git",
    worktree_path=Path("/path/to/worktree"),
    github_token=token,
    claude_api_key=key
)

# Output:
# - Posts PR comment if blocker
# - Generates developer_handoff_pr28.md
# - Saves state to .qa_state_pr_28.json
# - Status: BLOCKED

# After developer fixes:
# Run again - it will:
# - Check if previous blockers resolved
# - Run tests if clear
# - Status: PASSED
```

## Benefits

1. **No wasted test runs** - Don't test if it can't work
2. **Clear developer feedback** - Exact files and instructions
3. **Autonomous loop** - Dev agent → QA agent → Dev agent
4. **Memory** - Doesn't repeat checks unnecessarily
5. **Repo context** - Always includes which repo/PR for routing

## Example Output

**Blocker Report:**
```
🚫 Cannot test PR #28
Repository: Sanchay-T/ob1-sandbox
Issue: Components not integrated into routing
Fix: Add BrowserRouter to App.jsx
Handoff file: developer_handoff_pr28.md
```

**Success Report:**
```
✅ QA PASSED for PR #28
Repository: Sanchay-T/ob1-sandbox
Previous blocker (missing_routing) was fixed!
Tests: 5/5 passed
Videos: dashboard-test.webm shows full flow
```

---

This creates a **complete autonomous development loop** where agents fix each other's issues!
