"""
Complete Playwright Example for Stage 2 - Frontend Testing with Video Recording

This script demonstrates:
1. Starting a development server (npm run dev)
2. Waiting for the server to be ready
3. Recording video of browser interactions
4. Taking screenshots
5. Testing a login flow
6. Proper cleanup

Usage:
    python playwright_example.py

Requirements:
    pip install playwright
    playwright install chromium
"""

import subprocess
import time
import socket
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext


class DevServer:
    """Manages development server lifecycle."""

    def __init__(self, app_dir: str, port: int = 3000, command: str = "npm run dev"):
        self.app_dir = Path(app_dir)
        self.port = port
        self.command = command.split()
        self.process = None

    def start(self):
        """Start the development server."""
        print(f"Starting dev server in {self.app_dir}...")

        self.process = subprocess.Popen(
            self.command,
            cwd=self.app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for server to be ready
        if not self._wait_for_port(timeout=60):
            self.stop()
            raise TimeoutError(f"Server did not start on port {self.port} within 60 seconds")

        print(f"✓ Server is ready at http://localhost:{self.port}")

    def stop(self):
        """Stop the development server."""
        if self.process:
            print("Stopping dev server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("✓ Server stopped")

    def _wait_for_port(self, timeout: int = 30) -> bool:
        """Wait for the port to be open."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_port_open():
                return True
            time.sleep(0.5)
        return False

    def _is_port_open(self) -> bool:
        """Check if the port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(("localhost", self.port))
            return result == 0
        finally:
            sock.close()


class PlaywrightRecorder:
    """Records browser interactions with Playwright."""

    def __init__(self, base_url: str, headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.video_dir = Path("videos")
        self.screenshot_dir = Path("screenshots")
        self.trace_dir = Path("traces")

        # Create output directories
        self.video_dir.mkdir(exist_ok=True)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.trace_dir.mkdir(exist_ok=True)

    def record_session(self):
        """Record a complete test session."""
        with sync_playwright() as p:
            print(f"\nLaunching browser (headless={self.headless})...")

            # Launch browser
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-dev-shm-usage']  # Helps in CI/CD
            )

            # Create context with video recording
            context = browser.new_context(
                record_video_dir=str(self.video_dir),
                record_video_size={"width": 1920, "height": 1080},
                viewport={"width": 1920, "height": 1080}
            )

            # Start tracing for detailed debugging
            context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )

            page = context.new_page()

            try:
                # Run test scenarios
                self._test_homepage(page)
                self._test_navigation(page)
                self._test_login_flow(page)

                print("\n✓ All tests completed successfully!")

            except Exception as e:
                print(f"\n✗ Error during testing: {e}")
                page.screenshot(path=str(self.screenshot_dir / "error.png"))
                raise

            finally:
                # Stop tracing
                trace_path = self.trace_dir / "session-trace.zip"
                context.tracing.stop(path=str(trace_path))
                print(f"✓ Trace saved to: {trace_path}")

                # Get video path before closing
                video_path = page.video.path()

                # Close browser
                context.close()
                browser.close()

                print(f"✓ Video saved to: {video_path}")
                print(f"✓ Screenshots saved to: {self.screenshot_dir}/")

    def _test_homepage(self, page: Page):
        """Test 1: Homepage loads correctly."""
        print("\n[Test 1] Testing homepage...")

        page.goto(self.base_url)
        page.wait_for_load_state("networkidle")

        # Take screenshot
        page.screenshot(path=str(self.screenshot_dir / "01_homepage.png"))

        # Verify page loaded
        assert page.title(), "Page title is empty"
        print(f"  ✓ Homepage loaded: {page.title()}")

    def _test_navigation(self, page: Page):
        """Test 2: Navigation works."""
        print("\n[Test 2] Testing navigation...")

        # Example: Click on various navigation links
        # Adjust selectors based on your actual app

        # Try to find and click common navigation elements
        navigation_tests = [
            ("link", "About"),
            ("link", "Contact"),
            ("link", "Home"),
        ]

        for role, name in navigation_tests:
            try:
                link = page.get_by_role(role, name=name)
                if link.is_visible(timeout=2000):
                    link.click()
                    page.wait_for_load_state("domcontentloaded")
                    screenshot_name = f"02_nav_{name.lower()}.png"
                    page.screenshot(path=str(self.screenshot_dir / screenshot_name))
                    print(f"  ✓ Navigated to {name}")
            except Exception:
                print(f"  ⊘ Skipped {name} (not found)")

    def _test_login_flow(self, page: Page):
        """Test 3: Login flow (adjust based on your app)."""
        print("\n[Test 3] Testing login flow...")

        # Try to navigate to login page
        try:
            page.goto(f"{self.base_url}/login")
            page.wait_for_load_state("domcontentloaded")

            # Take screenshot of login page
            page.screenshot(path=str(self.screenshot_dir / "03_login_page.png"))

            # Try to fill login form (adjust selectors as needed)
            # This is a generic example - customize for your app

            # Example with common patterns:
            try:
                # Try by label
                email_input = page.get_by_label("Email", exact=False)
                password_input = page.get_by_label("Password", exact=False)
            except Exception:
                # Try by placeholder
                try:
                    email_input = page.get_by_placeholder("Email", exact=False)
                    password_input = page.get_by_placeholder("Password", exact=False)
                except Exception:
                    # Try by input type
                    email_input = page.locator('input[type="email"]').first
                    password_input = page.locator('input[type="password"]').first

            # Fill form
            email_input.fill("test@example.com")
            password_input.fill("password123")

            page.screenshot(path=str(self.screenshot_dir / "04_login_filled.png"))

            # Try to find and click submit button
            try:
                submit_button = page.get_by_role("button", name="Sign in", exact=False)
            except Exception:
                submit_button = page.locator('button[type="submit"]').first

            submit_button.click()

            # Wait a bit to see the result
            page.wait_for_timeout(2000)
            page.screenshot(path=str(self.screenshot_dir / "05_login_submitted.png"))

            print("  ✓ Login flow tested")

        except Exception as e:
            print(f"  ⊘ Login test skipped or failed: {e}")
            print("     (This is expected if your app doesn't have a /login route)")


def main():
    """Main execution function."""

    # Configuration
    APP_DIRECTORY = "./frontend"  # Adjust to your frontend app path
    BASE_URL = "http://localhost:3000"
    PORT = 3000
    HEADLESS = True  # Set to False to see the browser

    print("=" * 60)
    print("Playwright Frontend Testing & Recording Demo")
    print("=" * 60)

    # Option 1: Test with development server management
    # Uncomment this section if you want to auto-start the dev server

    # server = DevServer(app_dir=APP_DIRECTORY, port=PORT)
    # try:
    #     server.start()
    #     recorder = PlaywrightRecorder(base_url=BASE_URL, headless=HEADLESS)
    #     recorder.record_session()
    # finally:
    #     server.stop()

    # Option 2: Test with manually started server (recommended for first run)
    print("\n⚠ Make sure your development server is running!")
    print(f"   Expected URL: {BASE_URL}")
    print("\n   If not running, start it with:")
    print("   cd frontend && npm run dev\n")

    input("Press Enter when your server is ready (or Ctrl+C to cancel)...")

    recorder = PlaywrightRecorder(base_url=BASE_URL, headless=HEADLESS)

    try:
        recorder.record_session()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ Testing complete!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  - Videos: {Path('videos').absolute()}/")
    print(f"  - Screenshots: {Path('screenshots').absolute()}/")
    print(f"  - Traces: {Path('traces').absolute()}/")
    print(f"\nView trace with:")
    print(f"  playwright show-trace {Path('traces/session-trace.zip').absolute()}")
    print()


if __name__ == "__main__":
    main()
