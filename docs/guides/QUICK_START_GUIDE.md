# Playwright Quick Start Guide - Stage 2 Implementation

This guide will get you up and running with Playwright for automated testing and video recording in **under 10 minutes**.

## Prerequisites

- Python 3.8 or higher
- Node.js (for running your frontend app)
- A frontend application (React, Vue, etc.)

## Installation (2 minutes)

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Playwright with pytest
pip install pytest-playwright

# Install browser binaries
playwright install chromium

# For CI/CD, also install system dependencies
playwright install --with-deps chromium
```

## Verify Installation

```bash
# Check Playwright is installed
playwright --version

# Output: Version 1.54.0
```

## Quick Test (3 minutes)

### 1. Create a test file

Create `test_quick.py`:

```python
from playwright.sync_api import sync_playwright

def test_record_video():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Enable video recording
        context = browser.new_context(
            record_video_dir="videos/"
        )

        page = context.new_page()

        # Navigate and interact
        page.goto("https://playwright.dev")
        page.screenshot(path="screenshot.png")

        # Close to save video
        context.close()
        browser.close()

if __name__ == "__main__":
    test_record_video()
```

### 2. Run the test

```bash
python test_quick.py
```

✅ This will:
- Open a Chromium browser
- Navigate to playwright.dev
- Take a screenshot
- Record a video to `videos/` folder

## Test Your Frontend App (5 minutes)

### 1. Create `conftest.py`

```python
import pytest

@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:3000"

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_dir": "test-results/videos/",
        "record_video_size": {"width": 1920, "height": 1080}
    }
```

### 2. Create `test_my_app.py`

```python
import pytest
from playwright.sync_api import Page, expect

def test_homepage(page: Page, base_url: str):
    """Test homepage loads."""
    page.goto(base_url)
    expect(page).to_have_title(pytest.regex(r".+"))
    page.screenshot(path="test-results/homepage.png")

def test_login(page: Page, base_url: str):
    """Test login flow."""
    page.goto(f"{base_url}/login")

    # Fill form
    page.get_by_label("Email").fill("user@example.com")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign in").click()

    # Verify login
    page.wait_for_url("**/dashboard")
    page.screenshot(path="test-results/dashboard.png")
```

### 3. Run tests

```bash
# Start your app first
cd frontend && npm run dev

# In another terminal, run tests
pytest --video=on
```

## Directory Structure

After running tests, you'll have:

```
project/
├── test-results/
│   ├── videos/
│   │   └── test-video.webm
│   ├── screenshots/
│   │   ├── homepage.png
│   │   └── dashboard.png
│   └── traces/
├── conftest.py
├── test_my_app.py
└── pytest.ini
```

## Common Commands

```bash
# Run all tests
pytest

# Run with video (only on failure)
pytest --video=retain-on-failure

# Run with tracing (for debugging)
pytest --tracing=on

# Run in headed mode (see browser)
pytest --headed

# Run specific test
pytest test_my_app.py::test_homepage

# Run on different browser
pytest --browser firefox
pytest --browser webkit

# View trace
playwright show-trace test-results/traces/trace.zip
```

## GitHub Actions Setup (2 minutes)

Create `.github/workflows/tests.yml`:

```yaml
name: Playwright Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        playwright install --with-deps chromium

    - name: Run tests
      run: pytest --video=retain-on-failure

    - name: Upload results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results
        path: test-results/
```

## Best Practices Checklist

- ✅ Use `page.get_by_role()`, `page.get_by_label()` for selectors
- ✅ Enable video only on failures in CI: `--video=retain-on-failure`
- ✅ Use `expect()` for assertions instead of `assert`
- ✅ Always close context to save videos: `context.close()`
- ✅ Use fixtures for common setup (authentication, base URL)
- ✅ Enable tracing for debugging flaky tests
- ✅ Run headless in CI: `browser.launch(headless=True)`

## Troubleshooting

### Video not saved
**Problem**: Video file not appearing
**Solution**: Ensure you call `context.close()` before the script ends

### Tests timeout
**Problem**: Tests hang or timeout
**Solution**: Check server is running, increase timeout:
```python
page.goto(url, timeout=60000)
```

### Selector not found
**Problem**: Element not found
**Solution**: Use Playwright Inspector:
```bash
PWDEBUG=1 pytest test_my_app.py
```

### CI/CD fails
**Problem**: Works locally but fails in CI
**Solution**: Install system dependencies:
```bash
playwright install --with-deps
```

## Next Steps

1. ✅ Read full documentation: `PLAYWRIGHT_RESEARCH.md`
2. ✅ Review complete examples: `playwright_example.py` and `pytest_example.py`
3. ✅ Check GitHub Actions templates: `github_actions_examples.yml`
4. ✅ Implement authentication: Use storage state for faster tests
5. ✅ Add to CI/CD: Set up GitHub Actions workflow
6. ✅ Explore advanced features: Network interception, mobile emulation

## Resources

- **Documentation**: https://playwright.dev/python/
- **API Reference**: https://playwright.dev/python/docs/api/class-playwright
- **Examples Repository**: https://github.com/microsoft/playwright-python
- **Discord Community**: https://aka.ms/playwright/discord

## File Overview

This repository contains:

1. **PLAYWRIGHT_RESEARCH.md** - Complete documentation (13 sections, 1000+ lines)
2. **QUICK_START_GUIDE.md** - This file (get started in 10 minutes)
3. **playwright_example.py** - Standalone script with server management
4. **pytest_example.py** - Pytest fixtures and test examples
5. **github_actions_examples.yml** - 10 different CI/CD workflows

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review error messages in test output
3. Enable debug mode: `PWDEBUG=1 pytest`
4. View traces: `playwright show-trace trace.zip`
5. Check Playwright docs: https://playwright.dev/python/

---

**Ready to start?** Run the Quick Test section above and you'll have your first recorded test in under 3 minutes!
