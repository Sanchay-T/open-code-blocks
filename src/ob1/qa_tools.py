"""
QA Agent Tools - Provides autonomous QA agent with tools to analyze PRs and generate tests
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import AssistantMessage, TextBlock, query as claude_query
from rich.console import Console

from .github_api import GitHubAPI, RepoRef, parse_github_repo


class AnalyzePRTool:
    """
    Enhanced PR Analyzer - Fetches actual file contents and extracts code snippets

    This tool provides deep analysis of PR changes by:
    - Fetching full file contents for key files
    - Extracting meaningful code snippets from diffs
    - Identifying components and their types
    - Returning rich context for test generation
    """

    name = "analyze_pr"
    description = "Analyzes a Pull Request to understand what files changed and what feature was added. Returns PR metadata, changed files, and diff content."

    def __init__(self, github_token: str, repo_url: str):
        self.github_token = github_token
        self.repo_url = repo_url
        self.owner, self.repo_name = parse_github_repo(repo_url)

    async def run(self, pr_number: int, fetch_contents: bool = True) -> dict[str, Any]:
        """
        Fetch PR data from GitHub API with optional deep analysis

        Args:
            pr_number: Pull request number
            fetch_contents: Whether to fetch full file contents (slower but more accurate)

        Returns:
            Dict with pr_data, files, code snippets, and analysis
        """
        repo_ref = RepoRef(owner=self.owner, name=self.repo_name, origin_url=self.repo_url)

        async with GitHubAPI(self.github_token) as gh:
            pr_data = await gh.get_pull_request(repo_ref, pr_number)
            files = await gh.list_pull_files(repo_ref, pr_number)

            # Optionally fetch full file contents for key files
            files_with_content = []
            for file in files:
                file_data = dict(file)

                # Fetch content for code files (skip very large files)
                if fetch_contents and file.get("additions", 0) + file.get("deletions", 0) < 500:
                    filename = file.get("filename", "")
                    if any(filename.endswith(ext) for ext in [".tsx", ".ts", ".jsx", ".js", ".py"]):
                        try:
                            content = await gh.get_file_content(repo_ref, filename, pr_data["head"]["sha"])
                            if content:
                                file_data["full_content"] = content
                        except Exception:
                            # If fetching fails, continue without content
                            pass

                files_with_content.append(file_data)

        # Extract component/feature information from changed files
        changed_components = []
        file_types = {"jsx": 0, "tsx": 0, "css": 0, "js": 0, "ts": 0}
        code_snippets = []

        for file in files_with_content:
            filename = file.get("filename", "")

            # Extract component name
            if "/" in filename:
                component_name = filename.split("/")[-1].replace(".jsx", "").replace(".tsx", "").replace(".css", "").replace(".js", "").replace(".ts", "")
                changed_components.append(component_name)

            # Track file types
            for ext in file_types:
                if filename.endswith(f".{ext}"):
                    file_types[ext] += 1

            # Extract meaningful code snippets from patch
            patch = file.get("patch", "")
            if patch:
                # Get added lines (lines starting with +)
                added_lines = [line[1:] for line in patch.split("\n") if line.startswith("+") and not line.startswith("+++")]
                if added_lines:
                    snippet = "\n".join(added_lines[:20])  # First 20 added lines
                    code_snippets.append({
                        "file": filename,
                        "snippet": snippet,
                        "additions": file.get("additions", 0)
                    })

        return {
            "pr_number": pr_number,
            "title": pr_data.get("title", ""),
            "description": pr_data.get("body", ""),
            "author": pr_data.get("user", {}).get("login", ""),
            "files": files_with_content,
            "changed_components": list(set(changed_components)),
            "file_types": file_types,
            "code_snippets": code_snippets[:10],  # Top 10 snippets
            "total_additions": sum(f.get("additions", 0) for f in files),
            "total_deletions": sum(f.get("deletions", 0) for f in files),
            "head_sha": pr_data["head"]["sha"],
            "base_sha": pr_data["base"]["sha"]
        }


class RouteDetectorTool:
    """
    Intelligent Route Detector - Discovers app routing structure dynamically

    Analyzes codebase to understand:
    - React Router, Next.js, or other routing patterns
    - Component-to-route mappings
    - Protected vs. public routes
    - Nested route structures
    """

    name = "detect_routes"
    description = "Analyzes routing configuration to build a site map of the application"

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path
        self.frontend_dir = worktree_path / "frontend"

    def run(self, pr_analysis: dict[str, Any]) -> dict[str, Any]:
        """
        Detect routes from codebase

        Args:
            pr_analysis: Output from AnalyzePRTool with file contents

        Returns:
            Dict with route mappings, routing pattern, and component locations
        """
        routes = {}
        routing_pattern = "unknown"

        # Strategy 1: Look for explicit routing files in changed files
        routing_files = []
        for file in pr_analysis.get("files", []):
            filename = file.get("filename", "").lower()
            if any(pattern in filename for pattern in ["route", "router", "app.tsx", "app.jsx"]):
                routing_files.append(file)

        # Strategy 2: If no routing files in PR, search the frontend directory
        if not routing_files:
            potential_files = [
                self.frontend_dir / "src" / "App.tsx",
                self.frontend_dir / "src" / "App.jsx",
                self.frontend_dir / "src" / "routes.ts",
                self.frontend_dir / "src" / "routes.tsx",
                self.frontend_dir / "src" / "router" / "index.ts",
                self.frontend_dir / "pages" / "_app.tsx",  # Next.js
            ]

            for path in potential_files:
                if path.exists():
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    routing_files.append({
                        "filename": str(path.relative_to(self.worktree_path)),
                        "full_content": content
                    })

        # Parse routing files
        for file in routing_files:
            content = file.get("full_content", "")
            if not content:
                continue

            # Detect React Router patterns
            if "react-router" in content.lower() or "<route" in content.lower():
                routing_pattern = "react-router"
                routes.update(self._parse_react_router(content))

            # Detect Next.js file-based routing
            if "_app" in file.get("filename", "") or "pages/" in file.get("filename", ""):
                routing_pattern = "nextjs"
                # Next.js uses file-based routing, would need directory scan
                # For now, fallback to simple detection

        # Strategy 3: Infer routes from component files in PR
        for file in pr_analysis.get("files", []):
            filename = file.get("filename", "")
            content = file.get("full_content", "")

            # Look for component files
            if filename.endswith((".tsx", ".jsx")):
                component_name = filename.split("/")[-1].replace(".tsx", "").replace(".jsx", "")

                # Try to infer route from component name
                if "login" in component_name.lower():
                    routes["/login"] = {"component": component_name, "file": filename, "protected": False}
                elif "dashboard" in component_name.lower():
                    routes["/dashboard"] = {"component": component_name, "file": filename, "protected": True}
                elif "home" in component_name.lower() or "landing" in component_name.lower():
                    routes["/"] = {"component": component_name, "file": filename, "protected": False}
                elif "footer" in component_name.lower() or "header" in component_name.lower() or "nav" in component_name.lower():
                    # These are typically not routes but shared components
                    pass
                else:
                    # Generic route inference
                    route_path = f"/{component_name.lower()}"
                    routes[route_path] = {"component": component_name, "file": filename, "protected": False}

        # If still no routes found, default to root
        if not routes:
            routes["/"] = {"component": "App", "file": "unknown", "protected": False}

        return {
            "routes": routes,
            "routing_pattern": routing_pattern,
            "route_count": len(routes),
            "detected_from": "pr_files" if routing_files else "inference"
        }

    def _parse_react_router(self, content: str) -> dict[str, dict]:
        """Parse React Router patterns from code"""
        import re

        routes = {}

        # Pattern 1: <Route path="/dashboard" element={<Dashboard />} />
        pattern1 = r'<Route\s+path=["\']([^"\']+)["\']\s+(?:element=\{<(\w+)[^}]*\/?>|component=\{?(\w+)\}?)'
        matches = re.findall(pattern1, content)
        for match in matches:
            path = match[0]
            component = match[1] or match[2]
            routes[path] = {"component": component, "file": "unknown", "protected": False}

        # Pattern 2: { path: '/dashboard', component: Dashboard }
        pattern2 = r'\{\s*path:\s*["\']([^"\']+)["\']\s*,\s*component:\s*(\w+)'
        matches = re.findall(pattern2, content)
        for match in matches:
            path, component = match
            routes[path] = {"component": component, "file": "unknown", "protected": False}

        # Pattern 3: Check for ProtectedRoute or RequireAuth wrappers
        if "ProtectedRoute" in content or "RequireAuth" in content or "PrivateRoute" in content:
            # Mark routes inside protected wrappers
            for path in routes:
                if path != "/" and path != "/login":
                    routes[path]["protected"] = True

        return routes


class AuthDetectorTool:
    """
    Authentication Pattern Detector - Identifies auth requirements

    Analyzes codebase to understand:
    - Presence of authentication system
    - Login flow and credentials
    - Protected route patterns
    - Auth state management approach
    """

    name = "detect_auth"
    description = "Detects authentication patterns and requirements in the application"

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path
        self.frontend_dir = worktree_path / "frontend"

    def run(self, pr_analysis: dict[str, Any], route_info: dict[str, Any]) -> dict[str, Any]:
        """
        Detect authentication patterns

        Args:
            pr_analysis: Output from AnalyzePRTool
            route_info: Output from RouteDetectorTool

        Returns:
            Dict with auth info, login flow, and protected routes
        """
        has_auth = False
        login_route = None
        login_component = None
        auth_pattern = "none"
        protected_routes = []
        login_fields = []

        # Check if any routes are marked as protected
        routes = route_info.get("routes", {})
        protected_routes = [path for path, info in routes.items() if info.get("protected")]

        # Look for auth-related files and patterns
        for file in pr_analysis.get("files", []):
            filename = file.get("filename", "").lower()
            content = file.get("full_content", "")

            # Detect login component
            if "login" in filename:
                has_auth = True
                login_component = file.get("filename")
                login_route = "/login"  # Default assumption

                # Look for form fields in content
                if content:
                    if "email" in content.lower() or "username" in content.lower():
                        login_fields.append("email")
                    if "password" in content.lower():
                        login_fields.append("password")

            # Detect auth patterns
            if content:
                if "useAuth" in content or "AuthContext" in content:
                    auth_pattern = "context"
                elif "useSelector" in content and "auth" in content.lower():
                    auth_pattern = "redux"
                elif "getSession" in content or "useSession" in content:
                    auth_pattern = "next-auth"

        # If protected routes exist but no login found, check common locations
        if protected_routes and not has_auth:
            login_candidates = [
                self.frontend_dir / "src" / "components" / "Login.tsx",
                self.frontend_dir / "src" / "pages" / "Login.tsx",
                self.frontend_dir / "src" / "Login.tsx",
            ]

            for path in login_candidates:
                if path.exists():
                    has_auth = True
                    login_component = str(path.relative_to(self.worktree_path))
                    login_route = "/login"
                    break

        return {
            "has_authentication": has_auth,
            "login_route": login_route,
            "login_component": login_component,
            "auth_pattern": auth_pattern,
            "protected_routes": protected_routes,
            "login_fields": login_fields,
            "requires_login": len(protected_routes) > 0
        }


class GeneratePlaywrightTestTool:
    """
    Intelligent Test Generator - Creates Playwright tests with proper navigation

    Uses rich context to generate tests that:
    - Navigate to the CORRECT route (not hardcoded /)
    - Handle authentication when required
    - Test actual code changes
    - Use semantic selectors
    """

    name = "generate_playwright_test"
    description = "Generates Playwright test code for a specific component or feature. Takes component info and returns valid TypeScript test code."

    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key

    async def run(
        self,
        component_name: str,
        component_route: str,
        component_type: str,
        code_snippets: list[dict],
        auth_info: dict[str, Any],
        test_description: Optional[str] = None
    ) -> str:
        """
        Generate intelligent Playwright test code using Claude with rich context

        Args:
            component_name: Name of the component (e.g., "Footer", "Dashboard")
            component_route: Route where component lives (e.g., "/dashboard")
            component_type: Type of component (e.g., "footer", "navigation", "form", "dashboard")
            code_snippets: List of actual code changes from PR
            auth_info: Authentication information (requires_login, login_route, etc.)
            test_description: Optional description of what to test

        Returns:
            Valid Playwright TypeScript test code with proper navigation
        """
        # Format code snippets
        snippets_text = ""
        if code_snippets:
            snippets_text = "\n\n**Actual code changes:**\n"
            for snippet in code_snippets[:3]:  # Top 3 snippets
                snippets_text += f"\nFile: {snippet['file']}\n```\n{snippet['snippet'][:300]}\n```\n"

        # Format auth setup if needed
        auth_setup = ""
        if auth_info.get("requires_login") and component_route in auth_info.get("protected_routes", []):
            login_route = auth_info.get("login_route", "/login")
            auth_setup = f"""
**IMPORTANT: This route requires authentication!**

Before testing {component_route}, you MUST login first:

```typescript
// Helper function to login
async function login(page) {{
  await page.goto('{login_route}');
  await page.fill('[data-testid="email"], input[type="email"], input[name="email"]', 'test@example.com');
  await page.fill('[data-testid="password"], input[type="password"], input[name="password"]', 'password123');
  await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
  await page.waitForURL('**{component_route}**');  // Wait for redirect
}}
```

Include this login helper and call it before navigating to {component_route}.
"""

        # Escape route for regex (move outside f-string to avoid backslash issues)
        escaped_route = component_route.replace('/', '\\/')

        prompt = f"""You are generating a Playwright test for a React application.

## PR CHANGES ANALYSIS

Component being tested: **{component_name}**
Component location (route): **{component_route}**
Component type: {component_type}
{test_description if test_description else ""}

{snippets_text}

## NAVIGATION INSTRUCTIONS

🎯 **CRITICAL**: The {component_name} component is located at route **{component_route}**, NOT at "/" !

Your test MUST navigate to: **{component_route}**

{auth_setup}

## TEST GENERATION GUIDELINES

### 1. Correct Navigation
```typescript
// ✅ CORRECT: Navigate to the actual component route
await page.goto('{component_route}');

// ❌ WRONG: DO NOT navigate to root unless component is actually at root
await page.goto('/');  // WRONG unless component_route is '/'
```

### 2. Verify Correct Page
After navigation, verify you're on the right page:
```typescript
await expect(page).toHaveURL(/{escaped_route}/);
```

### 3. Component-Specific Testing

Based on the component type **{component_type}**:

**If footer/header**: Test visibility, copyright text, links
```typescript
await expect(page.locator('footer')).toBeVisible();
await expect(page.locator('footer')).toContainText('©');
```

**If dashboard**: Test metrics, cards, charts visibility
```typescript
await expect(page.locator('[class*="dashboard"]')).toBeVisible();
await expect(page.locator('[class*="metric"], [class*="card"]').first()).toBeVisible();
```

**If form**: Test form fields and submission
```typescript
await expect(page.locator('form')).toBeVisible();
await page.fill('[data-testid="input-field"]', 'test value');
```

**If navigation**: Test menu items and navigation
```typescript
const navItems = ['Home', 'About', 'Contact'];
for (const item of navItems) {{
  await expect(page.getByRole('link', {{ name: new RegExp(item, 'i') }})).toBeVisible();
}}
```

### 4. Selector Strategy
- First choice: `[data-testid="..."]`
- Second choice: Semantic selectors (`getByRole`, `getByLabel`)
- Third choice: Text content (`getByText`)
- Last resort: CSS classes (but prefer `[class*="..."]` for flexibility)

### 5. Test Structure
```typescript
import {{ test, expect }} from '@playwright/test';

// Include login helper if authentication required

test.describe('{component_name} Component', () => {{
  test('{component_name.lower()} displays correctly', async ({{ page }}) => {{
    // 1. Login if required
    {f"await login(page);" if auth_setup else ""}

    // 2. Navigate to correct route
    await page.goto('{component_route}');

    // 3. Verify correct page
    await expect(page).toHaveURL(/{escaped_route}/);

    // 4. Test component renders
    // (Add specific assertions based on actual code changes)

    // 5. Test functionality
    // (Add interaction tests if applicable)
  }});
}});
```

## OUTPUT REQUIREMENTS

Generate ONLY the TypeScript test code.
- Use the CORRECT route: {component_route}
- Include auth setup if provided above
- Test ACTUAL changes from the code snippets
- Use semantic, meaningful selectors
- Include proper assertions

DO NOT include explanations, only the test code."""

        # Set API key in environment
        os.environ["CLAUDE_API_KEY"] = self.claude_api_key
        os.environ.setdefault("ANTHROPIC_API_KEY", self.claude_api_key)

        # Use claude-agent-sdk query
        chunks = []
        async for message in claude_query(prompt=prompt):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)

        test_code = "\n".join(chunks).strip()

        # Clean up markdown code blocks if present
        if "```typescript" in test_code:
            test_code = test_code.split("```typescript")[1].split("```")[0].strip()
        elif "```ts" in test_code:
            test_code = test_code.split("```ts")[1].split("```")[0].strip()
        elif "```" in test_code:
            test_code = test_code.split("```")[1].split("```")[0].strip()

        return test_code


class WriteTestFileTool:
    """Tool to write generated test code to a file"""

    name = "write_test_file"
    description = "Writes Playwright test code to a file in the tests/qa directory. Returns the file path."

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path
        self.test_dir = worktree_path / "frontend" / "tests" / "qa"

    def run(self, test_code: str, test_name: str) -> str:
        """
        Write test code to file

        Args:
            test_code: TypeScript test code
            test_name: Name for the test file (without .spec.ts extension)

        Returns:
            Absolute path to created test file
        """
        # Ensure test directory exists
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Create test file
        test_file = self.test_dir / f"{test_name}.spec.ts"
        test_file.write_text(test_code, encoding="utf-8")

        return str(test_file)


class RunPlaywrightTestTool:
    """Tool to execute Playwright tests and capture results"""

    name = "run_playwright_test"
    description = "Runs Playwright tests and returns the results with video paths. Can run specific test file or all tests."

    def __init__(self, worktree_path: Path, console: Optional[Console] = None):
        self.worktree_path = worktree_path
        self.frontend_dir = worktree_path / "frontend"
        self.console = console or Console()

    def run(self, test_file: Optional[str] = None) -> dict[str, Any]:
        """
        Execute Playwright tests

        Args:
            test_file: Optional specific test file to run. If None, runs all tests.

        Returns:
            Dict with test results, exit code, stdout, stderr, and video paths
        """
        # Build command
        cmd = ["npx", "playwright", "test"]
        if test_file:
            # Get relative path from frontend dir
            if test_file.startswith(str(self.frontend_dir)):
                rel_path = Path(test_file).relative_to(self.frontend_dir)
                cmd.append(str(rel_path))
            else:
                cmd.append(test_file)

        self.console.print(f"[dim cyan]Running:[/dim cyan] {' '.join(cmd)}")

        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.frontend_dir),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            # Find video files
            video_dir = self.frontend_dir / "test-results"
            videos = []
            if video_dir.exists():
                videos = [str(p) for p in video_dir.glob("**/*.webm")]

            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "videos": videos,
                "video_count": len(videos)
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "passed": False,
                "stdout": "",
                "stderr": "Test execution timed out after 2 minutes",
                "videos": [],
                "video_count": 0
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "passed": False,
                "stdout": "",
                "stderr": str(e),
                "videos": [],
                "video_count": 0
            }


class ReadBuildLogsTool:
    """Tool to read and parse build logs"""

    name = "read_build_logs"
    description = "Reads build logs and extracts errors, warnings, and build status."

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path

    def run(self, log_file: str = "build.log", max_lines: int = 100) -> dict[str, Any]:
        """
        Read and parse build logs

        Args:
            log_file: Path to build log file (relative to worktree)
            max_lines: Maximum number of lines to read from end

        Returns:
            Dict with build status, errors, warnings, and log tail
        """
        log_path = self.worktree_path / log_file

        if not log_path.exists():
            return {
                "exists": False,
                "build_passed": None,
                "errors": [],
                "warnings": [],
                "log_tail": ""
            }

        # Read log file
        log_content = log_path.read_text(encoding="utf-8", errors="ignore")
        lines = log_content.splitlines()

        # Get tail
        tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        tail = "\n".join(tail_lines)

        # Parse for errors and warnings
        errors = [line for line in lines if "error" in line.lower() and not line.strip().startswith("//")]
        warnings = [line for line in lines if "warning" in line.lower() and not line.strip().startswith("//")]

        # Determine build status
        build_passed = "build complete" in log_content.lower() or "built in" in log_content.lower()
        build_failed = "build failed" in log_content.lower() or len(errors) > 0

        return {
            "exists": True,
            "build_passed": build_passed and not build_failed,
            "errors": errors[:10],  # First 10 errors
            "warnings": warnings[:10],  # First 10 warnings
            "error_count": len(errors),
            "warning_count": len(warnings),
            "log_tail": tail
        }


class ReadTestResultsTool:
    """Tool to read and parse Playwright test results"""

    name = "read_test_results"
    description = "Reads Playwright test results and extracts test status, passed/failed tests, and errors."

    def __init__(self, worktree_path: Path):
        self.worktree_path = worktree_path

    def run(self, log_file: str = "playwright.log", max_lines: int = 100) -> dict[str, Any]:
        """
        Read and parse test results

        Args:
            log_file: Path to test log file (relative to worktree)
            max_lines: Maximum number of lines to read from end

        Returns:
            Dict with test status, passed/failed counts, and log tail
        """
        log_path = self.worktree_path / log_file

        if not log_path.exists():
            return {
                "exists": False,
                "tests_passed": None,
                "passed_count": 0,
                "failed_count": 0,
                "tests": [],
                "log_tail": ""
            }

        # Read log file
        log_content = log_path.read_text(encoding="utf-8", errors="ignore")
        lines = log_content.splitlines()

        # Get tail
        tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        tail = "\n".join(tail_lines)

        # Parse test results
        passed_tests = []
        failed_tests = []

        for line in lines:
            if "✓" in line or "passed" in line.lower():
                passed_tests.append(line.strip())
            elif "✗" in line or "failed" in line.lower():
                failed_tests.append(line.strip())

        # Determine overall status
        all_passed = "passed" in log_content.lower() and failed_tests == []

        return {
            "exists": True,
            "tests_passed": all_passed,
            "passed_count": len(passed_tests),
            "failed_count": len(failed_tests),
            "passed_tests": passed_tests[:5],
            "failed_tests": failed_tests[:5],
            "log_tail": tail
        }


class VisualVerificationTool:
    """
    Visual Verification using Claude Vision API

    Takes screenshots and uses Claude's vision capabilities to:
    - Verify correct page navigation
    - Identify what's actually shown on screen
    - Compare to expected feature
    - Provide confidence scores and detailed analysis
    """

    name = "visual_verification"
    description = "Uses Claude vision API to analyze screenshots and verify correct page navigation"

    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key

    async def verify_navigation(
        self,
        screenshot_path: str,
        expected_feature: str,
        expected_route: str,
        component_type: str
    ) -> dict[str, Any]:
        """
        Verify navigation using screenshot analysis

        Args:
            screenshot_path: Path to screenshot file
            expected_feature: Expected feature name (e.g., "Dashboard", "Footer")
            expected_route: Expected route (e.g., "/dashboard")
            component_type: Type of component (e.g., "dashboard", "footer")

        Returns:
            Dict with verification result, confidence, and analysis
        """
        import base64

        # Read and encode screenshot
        screenshot_path_obj = Path(screenshot_path)
        if not screenshot_path_obj.exists():
            return {
                "correct_page": False,
                "confidence": 0.0,
                "actual_page": "unknown",
                "analysis": f"Screenshot not found at {screenshot_path}",
                "visible_elements": []
            }

        try:
            screenshot_b64 = base64.b64encode(screenshot_path_obj.read_bytes()).decode("utf-8")
        except Exception as e:
            return {
                "correct_page": False,
                "confidence": 0.0,
                "actual_page": "unknown",
                "analysis": f"Failed to read screenshot: {e}",
                "visible_elements": []
            }

        # Create vision prompt
        prompt = f"""Analyze this screenshot of a web application.

**Expected Information:**
- Feature: {expected_feature}
- Route: {expected_route}
- Component Type: {component_type}

**Your Task:**
Determine if this screenshot shows the {expected_feature} {component_type}.

**Analysis Questions:**
1. Is this the {expected_feature} page/component?
2. What page/component is actually shown in the screenshot?
3. Are there signs we're on the WRONG page? (e.g., login form when expecting dashboard, homepage when expecting settings, etc.)
4. What UI elements are visible?
5. What's your confidence level (0.0 to 1.0)?

**Respond in JSON format:**
```json
{{
  "correct_page": true/false,
  "actual_page": "description of what's shown",
  "confidence": 0.0-1.0,
  "visible_elements": ["list", "of", "visible", "elements"],
  "analysis": "detailed explanation of what you see and why you believe it's correct/incorrect"
}}
```

**Important Notes:**
- If you see a login form, footer alone doesn't count as being on the dashboard page
- If expecting dashboard but see a blank page or loading spinner, mark as incorrect
- If expecting footer component and it's visible at the bottom, mark as correct
- Be specific about what elements you see (buttons, cards, forms, headers, etc.)

Analyze the screenshot now:"""

        # Call Claude Vision API
        try:
            os.environ["CLAUDE_API_KEY"] = self.claude_api_key
            os.environ.setdefault("ANTHROPIC_API_KEY", self.claude_api_key)

            # Use Claude SDK to call vision API
            # NOTE: This is a simplified approach - in production, you'd use the official Anthropic client
            # For now, we'll create a text-based analysis request with the image
            from anthropic import Anthropic

            client = Anthropic(api_key=self.claude_api_key)

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse JSON from response
            # Look for JSON block in markdown
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text.strip()

            result = json.loads(json_text)

            return result

        except Exception as e:
            # Fallback if vision API fails
            return {
                "correct_page": None,
                "confidence": 0.0,
                "actual_page": "unknown",
                "analysis": f"Visual verification failed: {e}",
                "visible_elements": [],
                "error": str(e)
            }

    def find_screenshots(self, worktree_path: Path) -> list[str]:
        """
        Find all screenshots in test results directory

        Args:
            worktree_path: Path to worktree

        Returns:
            List of screenshot paths
        """
        screenshots = []
        test_results_dir = worktree_path / "frontend" / "test-results"

        if test_results_dir.exists():
            # Find all PNG screenshots
            screenshots.extend([str(p) for p in test_results_dir.glob("**/*.png")])

        return screenshots
