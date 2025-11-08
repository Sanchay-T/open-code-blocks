# Playwright Python Research for Stage 2 - Automated Testing & Video Recording

## Executive Summary

Playwright is a powerful Python library for automating browsers (Chromium, Firefox, WebKit) with comprehensive support for video recording, screenshots, and automated testing. This document provides complete setup instructions, code examples, and best practices for implementing automated UI testing with video recording for frontend applications.

---

## 1. Playwright Python Setup

### Installation

```bash
# Install Playwright with pytest plugin
pip install pytest-playwright

# Install browser binaries (Chromium, Firefox, WebKit)
playwright install

# Install system dependencies (recommended for CI/CD)
playwright install --with-deps

# Install specific browser only
playwright install chromium
```

### Requirements File
```txt
# requirements.txt
pytest==8.3.3
pytest-playwright==0.6.2
playwright==1.54.0
```

### Project Structure
```
project/
├── tests/
│   ├── test_frontend.py
│   ├── conftest.py
│   └── __init__.py
├── videos/
├── screenshots/
├── traces/
├── pytest.ini
└── requirements.txt
```

---

## 2. Complete Code Example: Recording Frontend App

### 2.1 Basic Video Recording (Synchronous)

```python
from playwright.sync_api import sync_playwright, Playwright

def record_frontend_app():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)

        # Create context with video recording enabled
        context = browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1920, "height": 1080}
        )

        # Create new page
        page = context.new_page()

        # Navigate to application
        page.goto("http://localhost:3000")

        # Perform interactions
        page.wait_for_load_state("networkidle")
        page.screenshot(path="screenshots/homepage.png")

        # Close context to save video
        context.close()
        browser.close()

if __name__ == "__main__":
    record_frontend_app()
```

### 2.2 Advanced Example with Subprocess Management

This example starts a development server, waits for it to be ready, performs tests with video recording, and cleans up:

```python
import subprocess
import time
import socket
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext

def is_port_open(host: str, port: int, timeout: int = 1) -> bool:
    """Check if a port is open and accepting connections."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()

def wait_for_server(host: str = "localhost", port: int = 3000, timeout: int = 30):
    """Wait for development server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_open(host, port):
            print(f"Server is ready at {host}:{port}")
            return True
        time.sleep(0.5)
    raise TimeoutError(f"Server did not start within {timeout} seconds")

def start_dev_server(cwd: str):
    """Start npm development server."""
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def record_and_test_frontend():
    """Complete example: Start server, record video, run tests, cleanup."""

    # Configuration
    app_directory = "/path/to/your/frontend/app"
    base_url = "http://localhost:3000"
    video_dir = "videos"
    screenshot_dir = "screenshots"

    # Create output directories
    Path(video_dir).mkdir(exist_ok=True)
    Path(screenshot_dir).mkdir(exist_ok=True)

    # Start development server
    print("Starting development server...")
    server_process = start_dev_server(app_directory)

    try:
        # Wait for server to be ready
        wait_for_server(port=3000, timeout=60)

        # Start Playwright automation
        with sync_playwright() as p:
            # Launch browser (headless=False to see what's happening)
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage']  # Useful for CI/CD
            )

            # Create context with video recording
            context = browser.new_context(
                record_video_dir=video_dir,
                record_video_size={"width": 1920, "height": 1080},
                viewport={"width": 1920, "height": 1080}
            )

            # Enable tracing for debugging
            context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )

            page = context.new_page()

            # Test scenario: Homepage
            print("Testing homepage...")
            page.goto(base_url)
            page.wait_for_load_state("networkidle")
            page.screenshot(path=f"{screenshot_dir}/01_homepage.png")

            # Test scenario: Navigation
            print("Testing navigation...")
            page.get_by_role("link", name="About").click()
            page.wait_for_load_state("domcontentloaded")
            page.screenshot(path=f"{screenshot_dir}/02_about_page.png")

            # Stop tracing and save
            context.tracing.stop(path="traces/trace.zip")

            # Close to save video
            video_path = page.video.path()
            context.close()
            browser.close()

            print(f"Video saved to: {video_path}")
            print("Test completed successfully!")

    finally:
        # Cleanup: Stop development server
        print("Stopping development server...")
        server_process.terminate()
        server_process.wait(timeout=10)
        print("Server stopped.")

if __name__ == "__main__":
    record_and_test_frontend()
```

### 2.3 Async Version

```python
import asyncio
from playwright.async_api import async_playwright

async def record_frontend_async():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1920, "height": 1080}
        )

        page = await context.new_page()
        await page.goto("http://localhost:3000")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="screenshots/homepage.png")

        # Get video path before closing
        video_path = await page.video.path()

        await context.close()
        await browser.close()

        print(f"Video saved to: {video_path}")

if __name__ == "__main__":
    asyncio.run(record_frontend_async())
```

---

## 3. Testing React/Vue Login Page

### 3.1 Login Test with Pytest

```python
# tests/test_login.py
import pytest
from playwright.sync_api import Page, expect

def test_login_success(page: Page):
    """Test successful login flow."""
    # Navigate to login page
    page.goto("http://localhost:3000/login")

    # Fill login form
    page.get_by_label("Email").fill("user@example.com")
    page.get_by_label("Password").fill("password123")

    # Submit form
    page.get_by_role("button", name="Sign in").click()

    # Verify successful login
    page.wait_for_url("**/dashboard")
    expect(page).to_have_url("http://localhost:3000/dashboard")

    # Take screenshot of dashboard
    page.screenshot(path="screenshots/dashboard_after_login.png")

def test_login_validation_errors(page: Page):
    """Test login form validation."""
    page.goto("http://localhost:3000/login")

    # Submit empty form
    page.get_by_role("button", name="Sign in").click()

    # Check for validation messages
    expect(page.get_by_text("Email is required")).to_be_visible()
    expect(page.get_by_text("Password is required")).to_be_visible()

def test_login_invalid_credentials(page: Page):
    """Test login with invalid credentials."""
    page.goto("http://localhost:3000/login")

    page.get_by_label("Email").fill("wrong@example.com")
    page.get_by_label("Password").fill("wrongpassword")
    page.get_by_role("button", name="Sign in").click()

    # Verify error message
    expect(page.get_by_text("Invalid credentials")).to_be_visible()
```

### 3.2 Reusable Authentication Helper

```python
# tests/conftest.py
import pytest
from playwright.sync_api import Page, BrowserContext

@pytest.fixture(scope="session")
def authenticated_context(browser):
    """Create an authenticated browser context that can be reused."""
    context = browser.new_context()
    page = context.new_page()

    # Perform login
    page.goto("http://localhost:3000/login")
    page.get_by_label("Email").fill("user@example.com")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/dashboard")

    # Save authentication state
    context.storage_state(path="auth.json")

    page.close()
    context.close()

    return "auth.json"

@pytest.fixture
def authenticated_page(browser, authenticated_context):
    """Provide a page with saved authentication state."""
    context = browser.new_context(storage_state=authenticated_context)
    page = context.new_page()
    yield page
    page.close()
    context.close()

def test_dashboard_with_auth(authenticated_page: Page):
    """Test that requires authentication."""
    authenticated_page.goto("http://localhost:3000/dashboard")
    # Test dashboard functionality...
```

### 3.3 Testing Different Form Frameworks

#### React (with data-testid)
```python
def test_react_login(page: Page):
    page.goto("http://localhost:3000/login")

    # Using test IDs (recommended for React)
    page.get_by_test_id("email-input").fill("user@example.com")
    page.get_by_test_id("password-input").fill("password123")
    page.get_by_test_id("login-button").click()

    expect(page.get_by_test_id("welcome-message")).to_be_visible()
```

#### Vue (with role-based selectors)
```python
def test_vue_login(page: Page):
    page.goto("http://localhost:3000/login")

    # Using semantic selectors
    page.locator('input[type="email"]').fill("user@example.com")
    page.locator('input[type="password"]').fill("password123")
    page.locator('button[type="submit"]').click()

    page.wait_for_selector(".dashboard-container")
```

---

## 4. Video Recording Configuration

### 4.1 Video Recording Options

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        # Required: Directory to save videos
        record_video_dir="videos/",

        # Optional: Video dimensions (default: viewport size scaled to 800x800)
        record_video_size={"width": 1920, "height": 1080},

        # Optional: Set viewport (affects video if size not specified)
        viewport={"width": 1920, "height": 1080}
    )

    page = context.new_page()

    # ... perform actions ...

    # Important: Video is saved only after context.close()
    video_path = page.video.path()  # Get path synchronously
    context.close()

    print(f"Video saved: {video_path}")
```

### 4.2 Async Video Path Retrieval

```python
async def get_video_path_async(page):
    """Get video path in async mode."""
    path = await page.video.path()
    return path
```

### 4.3 Video Recording with Pytest

```python
# pytest.ini
[pytest]
# Enable video recording for all tests
addopts = --video on

# Alternative: Only record on failure
# addopts = --video retain-on-failure
```

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure video recording for all tests."""
    return {
        **browser_context_args,
        "record_video_dir": "test-results/videos/",
        "record_video_size": {"width": 1280, "height": 720}
    }
```

---

## 5. Screenshot Management

### 5.1 Different Screenshot Types

```python
# Full page screenshot
page.screenshot(path="screenshots/fullpage.png", full_page=True)

# Viewport only (default)
page.screenshot(path="screenshots/viewport.png")

# Specific element
element = page.get_by_test_id("header")
element.screenshot(path="screenshots/header.png")

# Screenshot with quality control (JPEG)
page.screenshot(
    path="screenshots/compressed.jpg",
    type="jpeg",
    quality=80
)

# Screenshot to buffer (for uploading)
screenshot_bytes = page.screenshot()
```

### 5.2 Screenshot on Test Failure

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on test failure."""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            screenshot_dir = Path("test-results/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshot_dir / f"{item.name}_failure.png"
            page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved: {screenshot_path}")
```

---

## 6. Uploading Videos to GitHub / Cloud Storage

### 6.1 Upload to GitHub Releases

```python
import os
from github import Github

def upload_video_to_github(video_path: str, repo_name: str, tag: str):
    """Upload video to GitHub release."""
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)

    repo = g.get_repo(repo_name)
    release = repo.get_release(tag)

    with open(video_path, "rb") as f:
        release.upload_asset(
            video_path,
            content_type="video/webm",
            name=os.path.basename(video_path)
        )

    print(f"Video uploaded to release {tag}")
```

### 6.2 Upload to AWS S3

```python
import boto3
from pathlib import Path

def upload_to_s3(video_path: str, bucket_name: str, s3_key: str):
    """Upload video to AWS S3."""
    s3_client = boto3.client("s3")

    s3_client.upload_file(
        video_path,
        bucket_name,
        s3_key,
        ExtraArgs={
            "ContentType": "video/webm",
            "ACL": "public-read"  # Or 'private' as needed
        }
    )

    url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    print(f"Video uploaded: {url}")
    return url
```

### 6.3 Upload to Google Cloud Storage

```python
from google.cloud import storage

def upload_to_gcs(video_path: str, bucket_name: str, blob_name: str):
    """Upload video to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(video_path, content_type="video/webm")
    blob.make_public()

    url = blob.public_url
    print(f"Video uploaded: {url}")
    return url
```

---

## 7. CI/CD Integration (GitHub Actions)

### 7.1 Complete GitHub Actions Workflow

```yaml
# .github/workflows/playwright-tests.yml
name: Playwright Tests

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Node.js (for frontend app)
      uses: actions/setup-node@v4
      with:
        node-version: '18'

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Install Playwright browsers
      run: python -m playwright install --with-deps chromium

    - name: Install frontend dependencies
      run: npm ci
      working-directory: ./frontend

    - name: Start development server in background
      run: |
        npm run dev &
        npx wait-on http://localhost:3000 -t 60000
      working-directory: ./frontend

    - name: Run Playwright tests
      run: pytest --tracing=retain-on-failure --video=retain-on-failure
      env:
        PLAYWRIGHT_TEST_BASE_URL: http://localhost:3000

    - name: Upload test results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: playwright-results
        path: |
          test-results/
          videos/
          screenshots/
          traces/
        retention-days: 30

    - name: Upload videos to release (on tag)
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: videos/*.webm
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 7.2 Using Docker for Consistent Environment

```yaml
# .github/workflows/playwright-docker.yml
name: Playwright Tests (Docker)

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright/python:v1.54.0-noble
      options: --user 1001

    steps:
    - uses: actions/checkout@v4

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest --video=on

    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results
        path: test-results/
```

### 7.3 Matrix Testing (Multiple Browsers)

```yaml
name: Cross-Browser Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        playwright install --with-deps ${{ matrix.browser }}

    - name: Run tests on ${{ matrix.browser }}
      run: pytest --browser ${{ matrix.browser }}

    - name: Upload ${{ matrix.browser }} results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: results-${{ matrix.browser }}
        path: test-results/
```

---

## 8. Best Practices for Automated UI Testing

### 8.1 Test Structure

```python
# Good: Descriptive test names
def test_user_can_login_with_valid_credentials():
    pass

# Good: Arrange-Act-Assert pattern
def test_login_form_validation(page: Page):
    # Arrange
    page.goto("http://localhost:3000/login")

    # Act
    page.get_by_role("button", name="Sign in").click()

    # Assert
    expect(page.get_by_text("Email is required")).to_be_visible()
```

### 8.2 Selector Best Practices

```python
# Priority order for selectors:

# 1. BEST: User-visible text (accessible to screen readers)
page.get_by_role("button", name="Submit")
page.get_by_label("Email address")
page.get_by_text("Welcome")
page.get_by_placeholder("Enter email")

# 2. GOOD: Test IDs (stable, doesn't change with UI)
page.get_by_test_id("submit-button")

# 3. ACCEPTABLE: CSS/XPath (fragile, avoid if possible)
page.locator("button.submit")
page.locator("//button[@type='submit']")

# 4. AVOID: Text selectors without semantic meaning
page.locator("text=Click here")  # Use get_by_role instead
```

### 8.3 Waiting Strategies

```python
# Auto-waiting (preferred - Playwright waits automatically)
page.get_by_role("button").click()  # Waits until button is ready

# Explicit waits (when needed)
page.wait_for_selector(".loading-spinner", state="hidden")
page.wait_for_load_state("networkidle")
page.wait_for_url("**/dashboard")

# Wait for specific condition
page.wait_for_function("() => document.readyState === 'complete'")

# Timeout configuration
page.get_by_role("button").click(timeout=5000)  # 5 second timeout
```

### 8.4 Error Handling

```python
import pytest
from playwright.sync_api import Page, TimeoutError

def test_robust_navigation(page: Page):
    """Example of proper error handling."""
    try:
        page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
    except TimeoutError:
        # Take screenshot for debugging
        page.screenshot(path="screenshots/timeout_error.png")
        pytest.fail("Page failed to load within 30 seconds")

    # Verify page loaded correctly
    assert page.is_visible("h1"), "Main heading not found"
```

### 8.5 Page Object Model

```python
# pages/login_page.py
from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.email_input = page.get_by_label("Email")
        self.password_input = page.get_by_label("Password")
        self.submit_button = page.get_by_role("button", name="Sign in")
        self.error_message = page.locator(".error-message")

    def navigate(self):
        self.page.goto("http://localhost:3000/login")

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()

    def get_error_message(self) -> str:
        return self.error_message.text_content()

# tests/test_login_pom.py
from pages.login_page import LoginPage

def test_login_with_pom(page: Page):
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login("user@example.com", "password123")

    page.wait_for_url("**/dashboard")
    assert "dashboard" in page.url
```

### 8.6 Fixtures for Test Data

```python
# tests/conftest.py
import pytest

@pytest.fixture
def valid_user():
    return {
        "email": "user@example.com",
        "password": "password123"
    }

@pytest.fixture
def base_url():
    return "http://localhost:3000"

def test_login_with_fixtures(page: Page, base_url: str, valid_user: dict):
    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill(valid_user["email"])
    page.get_by_label("Password").fill(valid_user["password"])
    page.get_by_role("button", name="Sign in").click()
```

### 8.7 Parallel Testing

```python
# Install pytest-xdist
# pip install pytest-xdist

# Run tests in parallel (4 workers)
# pytest -n 4

# pytest.ini configuration
[pytest]
addopts = -n auto  # Use all available CPU cores
```

### 8.8 Test Isolation

```python
# Each test gets a fresh browser context automatically
def test_first(page: Page):
    page.goto("http://localhost:3000")
    # This test's state is isolated

def test_second(page: Page):
    page.goto("http://localhost:3000")
    # This test starts fresh, no shared state
```

---

## 9. Advanced Features

### 9.1 Network Interception

```python
def test_with_mocked_api(page: Page):
    """Mock API responses for testing."""

    # Intercept and mock API call
    def handle_route(route):
        if "api/users" in route.request.url:
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"users": [{"id": 1, "name": "Test User"}]}'
            )
        else:
            route.continue_()

    page.route("**/*", handle_route)
    page.goto("http://localhost:3000/users")
```

### 9.2 Trace Recording for Debugging

```python
def test_with_trace(page: Page, context):
    """Record trace for debugging."""
    context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True
    )

    # Your test actions
    page.goto("http://localhost:3000")
    page.get_by_role("button", name="Submit").click()

    # Save trace
    context.tracing.stop(path="traces/test-trace.zip")

    # View with: playwright show-trace traces/test-trace.zip
```

### 9.3 Mobile Emulation

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    iphone = p.devices["iPhone 12"]
    browser = p.chromium.launch()
    context = browser.new_context(**iphone)

    page = context.new_page()
    page.goto("http://localhost:3000")
    page.screenshot(path="screenshots/mobile-view.png")
```

### 9.4 Geolocation Testing

```python
def test_geolocation(browser):
    """Test with specific geolocation."""
    context = browser.new_context(
        geolocation={"longitude": -122.4194, "latitude": 37.7749},
        permissions=["geolocation"]
    )

    page = context.new_page()
    page.goto("http://localhost:3000/map")
```

---

## 10. Troubleshooting

### Common Issues

1. **Videos not saving**
   - Ensure `context.close()` is called
   - Check directory permissions
   - Verify disk space

2. **Tests timing out**
   - Increase timeout: `page.goto(url, timeout=60000)`
   - Check network connectivity
   - Use `wait_until="domcontentloaded"` instead of "networkidle"

3. **Flaky tests**
   - Use auto-waiting instead of manual sleeps
   - Avoid `time.sleep()`, use `page.wait_for_*()` methods
   - Ensure proper test isolation

4. **CI/CD failures**
   - Use `--with-deps` for system dependencies
   - Set headless mode: `browser.launch(headless=True)`
   - Increase timeouts in CI environment
   - Use Docker containers for consistency

---

## 11. Complete Example: Full Test Suite

```python
# tests/test_full_suite.py
import pytest
import subprocess
import time
from pathlib import Path
from playwright.sync_api import Page, expect, BrowserContext

class TestConfig:
    BASE_URL = "http://localhost:3000"
    VIDEO_DIR = "test-results/videos"
    SCREENSHOT_DIR = "test-results/screenshots"

@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Create output directories."""
    Path(TestConfig.VIDEO_DIR).mkdir(parents=True, exist_ok=True)
    Path(TestConfig.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "record_video_dir": TestConfig.VIDEO_DIR,
        "record_video_size": {"width": 1920, "height": 1080},
        "viewport": {"width": 1920, "height": 1080}
    }

class TestHomepage:
    """Test suite for homepage."""

    def test_homepage_loads(self, page: Page):
        """Verify homepage loads correctly."""
        page.goto(TestConfig.BASE_URL)
        expect(page).to_have_title("My App")
        page.screenshot(path=f"{TestConfig.SCREENSHOT_DIR}/homepage.png")

    def test_navigation_menu(self, page: Page):
        """Test main navigation."""
        page.goto(TestConfig.BASE_URL)

        # Test all navigation links
        nav_links = ["Home", "About", "Contact"]
        for link_text in nav_links:
            link = page.get_by_role("link", name=link_text)
            expect(link).to_be_visible()

class TestLoginFlow:
    """Test suite for authentication."""

    def test_successful_login(self, page: Page):
        """Test login with valid credentials."""
        page.goto(f"{TestConfig.BASE_URL}/login")

        page.get_by_label("Email").fill("user@example.com")
        page.get_by_label("Password").fill("password123")
        page.get_by_role("button", name="Sign in").click()

        page.wait_for_url("**/dashboard")
        expect(page).to_have_url(f"{TestConfig.BASE_URL}/dashboard")

        # Verify user is logged in
        expect(page.get_by_text("Welcome back")).to_be_visible()

    def test_login_validation(self, page: Page):
        """Test form validation."""
        page.goto(f"{TestConfig.BASE_URL}/login")
        page.get_by_role("button", name="Sign in").click()

        expect(page.get_by_text("Email is required")).to_be_visible()
        expect(page.get_by_text("Password is required")).to_be_visible()

    def test_logout(self, page: Page):
        """Test logout functionality."""
        # Login first
        page.goto(f"{TestConfig.BASE_URL}/login")
        page.get_by_label("Email").fill("user@example.com")
        page.get_by_label("Password").fill("password123")
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/dashboard")

        # Logout
        page.get_by_role("button", name="Logout").click()

        # Verify redirected to login
        expect(page).to_have_url(f"{TestConfig.BASE_URL}/login")

class TestFormInteractions:
    """Test suite for form interactions."""

    def test_contact_form_submission(self, page: Page):
        """Test contact form."""
        page.goto(f"{TestConfig.BASE_URL}/contact")

        page.get_by_label("Name").fill("John Doe")
        page.get_by_label("Email").fill("john@example.com")
        page.get_by_label("Message").fill("Test message")

        page.get_by_role("button", name="Send").click()

        expect(page.get_by_text("Message sent successfully")).to_be_visible()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

---

## 12. Quick Reference Commands

```bash
# Installation
pip install pytest-playwright
playwright install --with-deps

# Run all tests
pytest

# Run with video recording
pytest --video on

# Run with tracing
pytest --tracing on

# Run specific browser
pytest --browser webkit

# Run multiple browsers
pytest --browser chromium --browser firefox

# Run in headed mode (see browser)
pytest --headed

# Run parallel tests
pytest -n auto

# Run with specific base URL
pytest --base-url http://localhost:3000

# View trace file
playwright show-trace traces/trace.zip

# Generate test from browser
playwright codegen http://localhost:3000

# Save authentication state
playwright codegen --save-storage=auth.json http://localhost:3000

# List installed browsers
playwright install --list
```

---

## 13. Resources

- **Official Docs**: https://playwright.dev/python/
- **API Reference**: https://playwright.dev/python/docs/api/class-playwright
- **GitHub**: https://github.com/microsoft/playwright-python
- **Discord**: https://aka.ms/playwright/discord
- **Stack Overflow**: Tag `playwright-python`

---

## Summary

Playwright Python provides a comprehensive solution for:
- **Browser automation** across Chromium, Firefox, and WebKit
- **Video recording** of all test interactions
- **Screenshots** at any point in tests
- **Automated testing** with pytest integration
- **CI/CD integration** via GitHub Actions
- **Debugging tools** like traces and network inspection

The library is production-ready, well-documented, and actively maintained by Microsoft, making it an excellent choice for Stage 2 automated testing and video recording of frontend applications.
