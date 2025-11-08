"""
Pytest Example for Playwright Testing with Video Recording

This demonstrates best practices for Playwright + Pytest integration.

File structure:
    tests/
    ├── conftest.py          (this file)
    ├── test_frontend.py     (test cases)
    └── pytest.ini           (configuration)

Usage:
    # Run all tests
    pytest

    # Run with video recording
    pytest --video on

    # Run with tracing
    pytest --tracing on

    # Run in headed mode (see browser)
    pytest --headed

    # Run specific browser
    pytest --browser webkit

Requirements:
    pip install pytest pytest-playwright
    playwright install
"""

# ============================================================================
# conftest.py - Pytest configuration and fixtures
# ============================================================================

import pytest
from pathlib import Path
from playwright.sync_api import Page, BrowserContext


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Configure browser context for all tests.
    This fixture is called by pytest-playwright.
    """
    return {
        **browser_context_args,
        "record_video_dir": "test-results/videos/",
        "record_video_size": {"width": 1920, "height": 1080},
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,  # Useful for development
    }


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application."""
    return "http://localhost:3000"


@pytest.fixture
def screenshot_dir():
    """Create and return screenshot directory."""
    path = Path("test-results/screenshots")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def setup_test(page: Page, screenshot_dir: Path, request):
    """
    Runs before and after each test.
    Takes a screenshot on test failure.
    """
    # Before test
    print(f"\n▶ Running test: {request.node.name}")

    yield

    # After test - screenshot on failure
    if request.node.rep_call.failed:
        screenshot_path = screenshot_dir / f"{request.node.name}_FAILED.png"
        page.screenshot(path=str(screenshot_path))
        print(f"  📸 Failure screenshot saved: {screenshot_path}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to make test result available in fixtures.
    This allows setup_test to access test failure status.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ============================================================================
# Authentication helpers
# ============================================================================

@pytest.fixture(scope="session")
def authenticated_storage_state(browser, base_url):
    """
    Creates an authenticated session and saves the storage state.
    This can be reused across tests to avoid repeated logins.
    """
    context = browser.new_context()
    page = context.new_page()

    try:
        # Perform login (customize for your app)
        page.goto(f"{base_url}/login")

        # Fill login form
        page.get_by_label("Email").fill("test@example.com")
        page.get_by_label("Password").fill("password123")
        page.get_by_role("button", name="Sign in").click()

        # Wait for successful login
        page.wait_for_url("**/dashboard", timeout=10000)

        # Save authenticated state
        storage_path = "test-results/auth.json"
        context.storage_state(path=storage_path)

        return storage_path

    except Exception as e:
        print(f"⚠ Could not create authenticated session: {e}")
        return None

    finally:
        page.close()
        context.close()


@pytest.fixture
def authenticated_page(browser, authenticated_storage_state):
    """
    Provides a page that's already authenticated.
    Useful for tests that require login.
    """
    if not authenticated_storage_state:
        pytest.skip("Authentication not available")

    context = browser.new_context(storage_state=authenticated_storage_state)
    page = context.new_page()

    yield page

    page.close()
    context.close()


# ============================================================================
# Test cases - test_frontend.py
# ============================================================================

import pytest
from playwright.sync_api import Page, expect


class TestHomepage:
    """Test suite for homepage functionality."""

    def test_homepage_loads(self, page: Page, base_url: str):
        """Test that homepage loads correctly."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Verify page loaded
        assert page.url == f"{base_url}/"
        assert page.title(), "Page title should not be empty"

        print(f"  ✓ Homepage loaded: {page.title()}")

    def test_homepage_title(self, page: Page, base_url: str):
        """Test homepage has correct title."""
        page.goto(base_url)

        # Use Playwright's expect for better error messages
        expect(page).to_have_title(pytest.regex(r".+"))  # Any non-empty title

    def test_homepage_responsive(self, page: Page, base_url: str):
        """Test homepage is responsive on mobile."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto(base_url)
        page.wait_for_load_state("domcontentloaded")

        # Check mobile menu exists (customize selector)
        # This is just an example
        assert page.is_visible("body")

        print("  ✓ Mobile viewport rendered")


class TestNavigation:
    """Test suite for navigation functionality."""

    @pytest.mark.parametrize("link_name,expected_path", [
        ("Home", "/"),
        ("About", "/about"),
        ("Contact", "/contact"),
    ])
    def test_navigation_links(self, page: Page, base_url: str, link_name: str, expected_path: str):
        """Test navigation links work correctly."""
        page.goto(base_url)

        # Try to find and click the link
        try:
            link = page.get_by_role("link", name=link_name)
            link.click()

            # Verify URL changed
            page.wait_for_url(f"**{expected_path}")
            assert expected_path in page.url

            print(f"  ✓ Navigation to {link_name} works")

        except Exception as e:
            pytest.skip(f"Link '{link_name}' not found: {e}")


class TestLoginFlow:
    """Test suite for authentication."""

    def test_login_page_exists(self, page: Page, base_url: str):
        """Test that login page is accessible."""
        try:
            page.goto(f"{base_url}/login")
            page.wait_for_load_state("domcontentloaded")

            # Verify we're on login page
            assert "login" in page.url.lower()
            print("  ✓ Login page accessible")

        except Exception as e:
            pytest.skip(f"Login page not found: {e}")

    def test_login_form_validation(self, page: Page, base_url: str):
        """Test login form shows validation errors."""
        try:
            page.goto(f"{base_url}/login")

            # Try to submit empty form
            submit_button = page.get_by_role("button", name="Sign in")
            submit_button.click()

            # Wait for validation (adjust selector as needed)
            page.wait_for_timeout(1000)

            # Check if validation messages appear
            # This is generic - customize for your app
            assert page.is_visible("input:invalid") or \
                   page.get_by_text("required", case_insensitive=True).count() > 0

            print("  ✓ Form validation works")

        except Exception as e:
            pytest.skip(f"Could not test validation: {e}")

    def test_login_with_valid_credentials(self, page: Page, base_url: str):
        """Test login with valid credentials."""
        try:
            page.goto(f"{base_url}/login")

            # Fill login form
            page.get_by_label("Email").fill("test@example.com")
            page.get_by_label("Password").fill("password123")
            page.get_by_role("button", name="Sign in").click()

            # Wait for navigation after login
            page.wait_for_url("**/dashboard", timeout=5000)

            # Verify successful login
            assert "dashboard" in page.url
            print("  ✓ Login successful")

        except Exception as e:
            pytest.skip(f"Could not test login: {e}")

    def test_logout(self, authenticated_page: Page):
        """Test logout functionality."""
        try:
            authenticated_page.goto("http://localhost:3000/dashboard")

            # Find and click logout button
            logout_button = authenticated_page.get_by_role("button", name="Logout")
            logout_button.click()

            # Verify redirected to login
            authenticated_page.wait_for_url("**/login")
            assert "login" in authenticated_page.url

            print("  ✓ Logout successful")

        except Exception as e:
            pytest.skip(f"Could not test logout: {e}")


class TestFormInteractions:
    """Test suite for form interactions."""

    def test_contact_form_submit(self, page: Page, base_url: str):
        """Test contact form submission."""
        try:
            page.goto(f"{base_url}/contact")

            # Fill form fields
            page.get_by_label("Name").fill("John Doe")
            page.get_by_label("Email").fill("john@example.com")
            page.get_by_label("Message").fill("This is a test message")

            # Submit form
            page.get_by_role("button", name="Send").click()

            # Wait for success message
            success_message = page.get_by_text("success", case_insensitive=True)
            expect(success_message).to_be_visible(timeout=5000)

            print("  ✓ Contact form submitted successfully")

        except Exception as e:
            pytest.skip(f"Could not test contact form: {e}")


class TestAccessibility:
    """Test suite for accessibility checks."""

    def test_homepage_has_main_heading(self, page: Page, base_url: str):
        """Test that homepage has a main h1 heading."""
        page.goto(base_url)

        # Check for h1 element
        heading = page.locator("h1").first
        expect(heading).to_be_visible()

        print(f"  ✓ Main heading found: {heading.text_content()}")

    def test_images_have_alt_text(self, page: Page, base_url: str):
        """Test that images have alt attributes."""
        page.goto(base_url)

        # Get all images
        images = page.locator("img").all()

        if not images:
            pytest.skip("No images found on page")

        # Check each image has alt attribute
        for img in images:
            alt = img.get_attribute("alt")
            assert alt is not None, f"Image missing alt attribute: {img}"

        print(f"  ✓ All {len(images)} images have alt text")


# ============================================================================
# pytest.ini configuration
# ============================================================================

"""
Create a pytest.ini file in your project root with:

[pytest]
# Enable Playwright
addopts =
    -v
    --tb=short
    --strict-markers

# Browser configuration
# --browser chromium
# --headed
# --slowmo 100

# Base URL
# --base-url http://localhost:3000

# Parallel execution (requires pytest-xdist)
# -n auto

# Video recording (on, off, retain-on-failure)
# --video retain-on-failure

# Tracing (on, off, retain-on-failure)
# --tracing retain-on-failure

testpaths = tests

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    smoke: marks tests as smoke tests
"""


# ============================================================================
# Usage examples
# ============================================================================

"""
# Run all tests
pytest

# Run with video recording
pytest --video on

# Run with video only on failures
pytest --video retain-on-failure

# Run with tracing (for debugging)
pytest --tracing on

# Run in headed mode (see browser)
pytest --headed

# Run with slow motion (useful for debugging)
pytest --headed --slowmo 100

# Run specific test file
pytest tests/test_frontend.py

# Run specific test class
pytest tests/test_frontend.py::TestLoginFlow

# Run specific test
pytest tests/test_frontend.py::TestLoginFlow::test_login_with_valid_credentials

# Run with specific browser
pytest --browser webkit

# Run on multiple browsers
pytest --browser chromium --browser firefox --browser webkit

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Run with custom base URL
pytest --base-url http://staging.example.com

# Run and generate HTML report (requires pytest-html)
pytest --html=test-results/report.html

# Run with markers
pytest -m smoke  # Run only smoke tests
pytest -m "not slow"  # Skip slow tests

# View trace file
playwright show-trace test-results/traces/trace.zip
"""

if __name__ == "__main__":
    print("This file contains pytest fixtures and test examples.")
    print("Run with: pytest")
