# 🐛 ISSUES AND FIXES - Detailed Analysis

**Purpose:** Exact bugs, root causes, and step-by-step fixes
**Audience:** New AI agent needing to fix bugs immediately
**Priority Order:** Fix #1 → #2 → #3

---

## 🔴 CRITICAL ISSUE #1: Cursor Provider `apply_diff` Bug

### Error Message
```
ProviderResult.__init__() got an unexpected keyword argument 'apply_diff'
```

### When It Happens
- **Frequency:** 100% of Cursor runs
- **Last Seen:** 2025-11-09 during dashboard creation (PR #28 attempt)
- **Impact:** Cursor provider completely blocked

### Root Cause Analysis

**The Problem:**
The `ProviderResult` dataclass definition does NOT include an `apply_diff` field:

**File:** `src/ob1/providers/base.py` (lines 8-12)
```python
@dataclass
class ProviderResult:
    transcript_path: Path | None
    diff_text: str | None = None
    # ❌ NO apply_diff FIELD!
```

But the Cursor provider tries to pass it:

**File:** `src/ob1/providers/cursor.py` (lines 74-78)
```python
return ProviderResult(
    transcript_path=transcript_path,
    diff_text=diff_output,
    apply_diff=False,  # ❌ INVALID PARAMETER!
)
```

**Why This Exists:**
Looks like a legacy parameter from when ProviderResult supported different diff application modes. The field was removed from the dataclass but the provider code wasn't updated.

### The Fix

**Option 1: Remove the Parameter (RECOMMENDED)**

**File:** `src/ob1/providers/cursor.py`
**Line:** 74-78

**Before:**
```python
return ProviderResult(
    transcript_path=transcript_path,
    diff_text=diff_output,
    apply_diff=False,
)
```

**After:**
```python
return ProviderResult(
    transcript_path=transcript_path,
    diff_text=diff_output,
)
```

**Steps:**
1. Open `src/ob1/providers/cursor.py`
2. Go to line 77
3. Delete the line `apply_diff=False,`
4. Save
5. Test with: `ob1 run -m "test" -k 1 --providers cursor --dry-run`

**Estimated Time:** 30 seconds

---

**Option 2: Add Field to ProviderResult (NOT RECOMMENDED)**

Only do this if you need different diff application modes.

**File:** `src/ob1/providers/base.py`

**Before:**
```python
@dataclass
class ProviderResult:
    transcript_path: Path | None
    diff_text: str | None = None
```

**After:**
```python
@dataclass
class ProviderResult:
    transcript_path: Path | None
    diff_text: str | None = None
    apply_diff: bool = True
```

**But then you'd need to update orchestrator.py to respect this flag!**

**Verdict:** Just use Option 1. Simpler.

### Verification

**After Fix, Run:**
```bash
cd /Users/sanchay/Documents/open-code-blocks
source .venv/bin/activate
ob1 run -m "Add a test button to homepage" -k 1 \
  --providers cursor \
  --target https://github.com/Sanchay-T/ob1-sandbox.git \
  --scope "frontend/**" \
  --dry-run
```

**Expected Output:**
```
╭─ 🔵 Cursor-1 ──── 🔍 DRY-RUN ─╮
│ ...                            │
│ Dry-run completed              │
╰────────────────────────────────╯
```

**NOT:**
```
✗ failed: ProviderResult.__init__() got...
```

### Related Code

**All places that return ProviderResult:**
```bash
grep -r "return ProviderResult" src/ob1/providers/
```

**Output:**
```
src/ob1/providers/claude.py:64:        return ProviderResult(transcript_path=transcript_path)
src/ob1/providers/cursor.py:74:        return ProviderResult(...)  # ❌ BUG HERE
src/ob1/providers/cursor.py:98:        return ProviderResult(...)
src/ob1/providers/codex.py:78:         return ProviderResult(...)
```

**Action:** Check cursor.py line 98 too (might have same bug in another return path)

---

## 🔴 CRITICAL ISSUE #2: QA Workflow PATH Issue

### Error Message
```
Claude Code not found. Install with:
  npm install -g @anthropic-ai/claude-code
```

### When It Happens
- **Frequency:** 100% of GitHub Actions QA workflow runs
- **Last Seen:** Every PR to ob1-sandbox
- **Impact:** QA agent never posts reviews

### Root Cause Analysis

**The Problem:**
GitHub Actions workflow DOES install Claude Code CLI:

**File:** `ob1-sandbox/.github/workflows/qa.yml` (line 83-85)
```yaml
- name: Install Claude Code CLI
  run: |
    npm install -g @anthropic-ai/claude-code
```

This installs to `/usr/local/lib/node_modules/@anthropic-ai/claude-code/`

**But:** When Python's `claude-agent-sdk` tries to find `claude` binary, it's not in PATH!

**Why:**
npm global binaries go to a directory NOT in the default PATH for the Python step.

**Typical npm global bin location:**
```bash
$(npm bin -g)
# Usually: /usr/local/bin or ~/.npm-global/bin
```

But the Python step doesn't inherit this PATH.

### The Fix

**File:** `ob1-sandbox/.github/workflows/qa.yml`
**Line:** 87-100

**Before:**
```yaml
- name: Claude QA review
  if: always()
  env:
    CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    python -m pip install --upgrade pip
    export OB1_REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/Sanchay-T/open-code-blocks.git"
    python -m pip install "git+$OB1_REPO_URL@main#egg=ob1"
    ob1 qa --pr ${{ github.event.pull_request.number }} \
      --target https://github.com/${{ github.repository }}.git \
      --build-log build.log \
      --test-log playwright.log \
      --artifacts "playwright-report, playwright-test-results"
```

**After:**
```yaml
- name: Claude QA review
  if: always()
  env:
    CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    # Add npm global bin to PATH so claude CLI is found
    export PATH="$(npm bin -g):$PATH"

    python -m pip install --upgrade pip
    export OB1_REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/Sanchay-T/open-code-blocks.git"
    python -m pip install "git+$OB1_REPO_URL@main#egg=ob1"

    # Verify claude is in PATH (optional debug)
    which claude || echo "WARNING: claude not found!"

    ob1 qa --pr ${{ github.event.pull_request.number }} \
      --target https://github.com/${{ github.repository }}.git \
      --build-log build.log \
      --test-log playwright.log \
      --artifacts "playwright-report, playwright-test-results"
```

**Key Change:**
```bash
export PATH="$(npm bin -g):$PATH"
```

This adds npm's global bin directory to PATH BEFORE running ob1 qa.

### Steps to Apply Fix

**Location:** The fix needs to go into the **ob1-sandbox** repository, NOT open-code-blocks!

```bash
cd /Users/sanchay/Documents/ob1-sandbox
```

**Edit file:**
```bash
# Open in your editor
code .github/workflows/qa.yml  # or vim, nano, etc.
```

**Line 87-100:** Add the PATH export as shown above

**Commit:**
```bash
git add .github/workflows/qa.yml
git commit -m "fix: add npm bin to PATH for Claude CLI"
git push origin main
```

**Important:** This fix goes to the **sandbox repo**, not the ob1 repo!

### Verification

**After Fix:**
1. Create a test PR in ob1-sandbox (any small change)
2. Watch GitHub Actions run
3. Check "QA Login Video" workflow
4. Verify step "Claude QA review" succeeds
5. Check PR for auto-comment from Claude

**Expected:** PR comment appears with:
```
## QA Summary
...
Build Status: ✓ Passed
Test Status: ✓ All tests passed
...
```

### Alternative Fixes (Not Recommended)

**Alt 1: Hardcode PATH**
```yaml
export PATH="/usr/local/bin:$PATH"
```
**Problem:** Assumes npm installs to /usr/local/bin (not always true)

**Alt 2: Use npx**
```bash
npx -g @anthropic-ai/claude-code ...
```
**Problem:** claude-agent-sdk calls `claude` binary directly, can't use npx

**Alt 3: Install claude locally instead of globally**
```yaml
npm install @anthropic-ai/claude-code
export PATH="$PWD/node_modules/.bin:$PATH"
```
**Problem:** Unnecessary complexity

**Verdict:** Stick with `$(npm bin -g)` approach (dynamic, works everywhere)

---

## 🟡 MEDIUM ISSUE #3: Codex Diff Parsing Error

### Error Message
```
cannot access local variable 'source_file' where it is not associated with a value
```

### When It Happens
- **Frequency:** ~50% of Codex runs (intermittent)
- **Last Seen:** 2025-11-09 during dashboard creation
- **Impact:** Codex fails unpredictably

### Root Cause Analysis

**The Problem:**
This error comes from the `unidiff` library when parsing malformed diffs.

**Typical Flow:**
1. Codex (GPT-4o) generates a diff
2. OB1 extracts it: `extract_diff_block(response.content)`
3. OB1 parses it: `unidiff.PatchSet(diff_text)`
4. **Boom!** unidiff throws error if diff is malformed

**Why Codex Generates Bad Diffs:**
- LLM might use wrong diff format
- Missing `---` or `+++` headers
- Wrong line counts in hunks
- Invalid characters

**Stack Trace Location:**
```
unidiff/parser.py:123 in parse_hunk
    source_file.patch_info.append(...)
    ^^^^^^^^^^^  # 'source_file' not defined!
```

This happens when diff header is missing/malformed, so `source_file` never gets set.

### The Fix

**File:** `src/ob1/providers/codex.py`
**Line:** Around 60-78 (in the retry loop)

**Current Code:**
```python
diff_text = extract_diff_block(response.choices[0].message.content)
if diff_text:
    try:
        patch = unidiff.PatchSet(diff_text)  # ❌ CAN CRASH HERE
        if not patch:
            failure_reason = failure_reason or "diff did not contain any file changes"
            continue
```

**Improved Code:**
```python
diff_text = extract_diff_block(response.choices[0].message.content)
if diff_text:
    try:
        # Try to parse diff with better error handling
        try:
            patch = unidiff.PatchSet(diff_text)
        except (ValueError, UnboundLocalError, AttributeError) as parse_err:
            # Diff is malformed
            failure_reason = f"malformed diff: {str(parse_err)[:50]}"
            if attempt < self._max_attempts:
                # Let it retry with better instructions
                continue
            else:
                # Final attempt failed
                raise RuntimeError(f"Codex produced unparseable diff: {parse_err}")

        if not patch:
            failure_reason = failure_reason or "diff did not contain any file changes"
            continue
```

**What This Does:**
1. Catches the `UnboundLocalError` specifically
2. Treats it as a malformed diff (not a crash)
3. Lets Codex retry with better instructions
4. After max retries, raises clear error message

### Additional Improvement: Better Retry Prompt

When Codex fails due to bad diff, give it specific instructions:

**File:** `src/ob1/providers/codex.py`
**Method:** `_build_retry_instruction`

**Add:**
```python
if "malformed diff" in failure_reason:
    return """
    Your previous diff was malformed and couldn't be parsed.
    Please ensure your diff follows this EXACT format:

    ```diff
    diff --git a/path/to/file.js b/path/to/file.js
    --- a/path/to/file.js
    +++ b/path/to/file.js
    @@ -1,3 +1,4 @@
     existing line
    +new line
     another existing line
    ```

    Requirements:
    - Use '---' and '+++' headers
    - Include correct line counts in @@ @@
    - Start added lines with '+'
    - Start removed lines with '-'
    - Leave context lines unmodified
    """
```

### Estimated Effort
- **Quick Fix:** 5 minutes (just add error handling)
- **Full Fix:** 15 minutes (add better retry prompts)

### Verification

**Test:**
```bash
# Run Codex multiple times, should eventually succeed
for i in {1..5}; do
  ob1 run -m "Add a small comment to App.jsx" -k 1 \
    --providers codex \
    --target https://github.com/Sanchay-T/ob1-sandbox.git \
    --scope "frontend/**" \
    --dry-run
done
```

**Expected:** At least 3/5 succeed (or all 5 with retry logic)

---

## 🟢 MINOR ISSUE #4: Missing Metrics in Dashboard

### Description
The live dashboard panels show:
```
⏱  00:00  │  📝 0 files  │  🛠️  0 tools
```

Even for completed agents. Metrics aren't being tracked/updated.

### Root Cause
The orchestrator doesn't call `dashboard.update_agent()` with metrics during execution.

### The Fix

**File:** `src/ob1/orchestrator.py`
**Line:** Around 140-160 (in the agent completion handler)

**Add metrics tracking:**
```python
# After agent completes
if res.status == "success":
    # Calculate metrics from transcript
    file_count = len(list_changed_files(worktree))  # Or parse from result
    tool_count = len(provider_result.tools_used) if hasattr(provider_result, 'tools_used') else 0

    dashboard.update_agent(
        agent_name,
        status='success',
        activity='PR created successfully!',
        pr_url=res.pr_url,
        metrics={
            'elapsed': elapsed_time,
            'files': file_count,
            'tools': tool_count,
            'diff_lines': diff_line_count,
        }
    )
```

**Challenge:** Need to track metrics during execution, not just at the end.

**Better Approach:** Providers should emit progress events that orchestrator listens to.

**Priority:** LOW (cosmetic, doesn't block functionality)

---

## 📋 FIX PRIORITY SUMMARY

| Issue | Priority | Effort | Impact | Fix First? |
|-------|----------|--------|--------|------------|
| #1 Cursor `apply_diff` | 🔴 Critical | 30 sec | Blocks Cursor | ✅ YES |
| #2 QA PATH | 🔴 Critical | 1 min | Blocks QA | ✅ YES |
| #3 Codex parsing | 🟡 Medium | 5-15 min | 50% failure rate | ⏰ After #1,#2 |
| #4 Dashboard metrics | 🟢 Low | 30 min | Cosmetic | ⏰ Later |

## 🎯 QUICK FIX SCRIPT

Want to fix #1 and #2 in one go? Run this:

```bash
cd /Users/sanchay/Documents/open-code-blocks

# Fix #1: Cursor provider
sed -i '' '/apply_diff=False,/d' src/ob1/providers/cursor.py

echo "✅ Fixed Cursor provider"

# Fix #2: QA workflow (in sandbox repo)
cd /Users/sanchay/Documents/ob1-sandbox

# Add PATH export before ob1 qa line
sed -i '' '/python -m pip install --upgrade pip/i\
    export PATH="$(npm bin -g):$PATH"
' .github/workflows/qa.yml

echo "✅ Fixed QA workflow PATH"

# Commit the QA workflow fix
git add .github/workflows/qa.yml
git commit -m "fix: add npm bin to PATH for Claude CLI"
git push origin main

echo "🎉 All critical fixes applied!"
```

**Then test:**
```bash
cd /Users/sanchay/Documents/open-code-blocks
source .venv/bin/activate
ob1 run -m "Add a test component" -k 3 \
  --target https://github.com/Sanchay-T/ob1-sandbox.git \
  --scope "frontend/**" \
  --dry-run
```

**Expected:** All 3 agents succeed (no errors!)

---

**END OF ISSUES AND FIXES**

*Next: Fix these bugs, then read CODEBASE_STATE.md for architecture*
