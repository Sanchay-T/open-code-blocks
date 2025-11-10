# ⚠️ STAGE 2: QA TESTING AGENT - STATUS

**Status:** CODED but NOT WORKING (PATH issue)
**Success Criteria:** PR gets auto-comment with Claude review + video
**Completion:** ~80% (code exists, workflow blocked)

---

## WHAT WAS BUILT

Automated QA agent that:
1. Reviews every PR with Claude
2. Builds the app
3. Runs Playwright tests
4. Records video
5. Posts review comment

**Trigger:** Any PR to `main` in ob1-sandbox

---

## HOW IT SHOULD WORK

### GitHub Actions Workflow
**File:** `ob1-sandbox/.github/workflows/qa.yml`

**Steps:**
1. Checkout code
2. Install Node.js deps
3. Install Playwright browsers
4. Build frontend (`npm run build → build.log`)
5. Start preview server (port 4173)
6. Run Playwright tests (`npx playwright test → playwright.log`)
7. Upload videos as artifacts
8. **Install Claude CLI** ← Works
9. **Run ob1 qa** ← ❌ FAILS (can't find `claude` binary)

### OB1 QA Command
**File:** `src/ob1/qa_agent.py`

**What it does:**
```python
async def run_qa_review(config):
    # 1. Fetch PR metadata from GitHub API
    pr = await gh.get_pull_request(repo, pr_number)
    files = await gh.list_pr_files(repo, pr_number)

    # 2. Read build/test logs
    build_log = read_file("build.log")[-6000:]  # Tail
    test_log = read_file("playwright.log")[-6000:]

    # 3. Build Claude prompt
    prompt = f"""
    You are OB1 QA, an elite frontend reviewer.
    PR: {pr.title}
    Files changed: {files}
    Build log: {build_log}
    Test log: {test_log}

    Provide:
    1. Summary of changes
    2. QA status (pass/fail)
    3. Blocking issues
    4. UX wins
    """

    # 4. Run Claude
    review = await claude_ping(prompt)

    # 5. Post comment to PR
    await gh.create_pr_comment(repo, pr_number, review)
```

---

## WHAT'S WORKING

✅ **ob1 qa CLI command** - Exists, runs locally
✅ **GitHub Actions workflow** - Syntactically correct
✅ **Playwright tests** - Configured, record video
✅ **Claude prompt engineering** - Good prompt template
✅ **GitHub API integration** - Can fetch PR, post comments
✅ **Artifact upload** - Videos saved

---

## WHAT'S BROKEN

### Critical: PATH Issue
**Error:** `Claude Code not found`

**Problem:**
Workflow installs Claude CLI:
```yaml
npm install -g @anthropic-ai/claude-code
```

But when Python runs `ob1 qa`, it can't find `claude` binary.

**Root Cause:**
npm global bin directory not in PATH for Python step.

**Fix:**
```yaml
- name: Claude QA review
  run: |
    export PATH="$(npm bin -g):$PATH"  # ← ADD THIS
    ob1 qa ...
```

**Impact:** Blocks ALL QA reviews in CI/CD

---

## WHAT'S NEVER BEEN TESTED

- [ ] End-to-end workflow (never succeeded)
- [ ] Claude review quality
- [ ] Video artifacts actually work
- [ ] Comment posting works
- [ ] Error handling in workflow

**Status:** All code exists, just never run successfully.

---

## PLAYWRIGHT TESTS

**File:** `ob1-sandbox/frontend/tests/qa/login.spec.ts`

**Test:**
```typescript
test('login page renders', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});
```

**Config:** `playwright.config.ts`
```typescript
use: {
  video: 'on',          // Record all tests
  screenshot: 'on',     // Capture screenshots
  trace: 'retain-on-failure',
}
```

**Output:**
- Videos: `test-results/**/video.webm`
- Report: `playwright-report/index.html`
- Both uploaded as GitHub Actions artifacts

---

## HOW TO FIX & TEST

### Fix (5 minutes)
1. Edit `ob1-sandbox/.github/workflows/qa.yml`
2. Line 87-100: Add PATH export (see ISSUES_AND_FIXES.md)
3. Commit + push to main

### Test (10 minutes)
1. Create dummy PR in ob1-sandbox:
   ```bash
   cd /Users/sanchay/Documents/ob1-sandbox
   git checkout -b test-qa-workflow
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: validate QA workflow"
   git push origin test-qa-workflow
   ```
2. Open PR on GitHub
3. Watch Actions tab
4. Verify "QA Login Video" workflow succeeds
5. Check PR for auto-comment from Claude

**Expected Result:**
PR comment appears:
```
## QA Summary

**Status:** ✓ Pass

**Changes:**
- Updated README.md

**Build:** ✓ Passed
**Tests:** ✓ All tests passed

**Review:**
[Claude's analysis here]

**Artifacts:** 
- Playwright Report
- Test Videos
```

---

## VALUE PROPOSITION

Once working, this provides:
- ✅ Instant PR feedback (no waiting for human review)
- ✅ Build verification (catches compile errors)
- ✅ Test verification (catches regressions)
- ✅ Video proof (see the app working)
- ✅ AI analysis (Claude's perspective)

**ROI:** High - automates entire QA process

---

## ALTERNATIVES CONSIDERED

### Why Claude CLI?
**Pros:** Full Agent SDK access, tool use, file operations
**Cons:** Requires Node.js binary

**Alternative:** Direct API calls
**Rejected:** Can't do file reads, git ops, build verification

### Why Playwright?
**Pros:** Best video recording, cross-browser
**Cons:** Slow setup (~30s for browser install)

**Alternative:** Cypress
**Rejected:** Playwright has better CI/CD support

---

**CONCLUSION:** Fix PATH issue → Stage 2 complete. ~5 min work.
