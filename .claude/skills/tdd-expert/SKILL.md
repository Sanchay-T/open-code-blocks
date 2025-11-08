# TDD Expert Skill

## Overview

Complete Test-Driven Development (TDD) workflow automation and enforcement. This skill ensures strict adherence to the RED-GREEN-REFACTOR cycle, guiding developers through proper TDD methodology with automated checks and best practices.

## Core Philosophy

**The Golden Rule:** NEVER write production code without a failing test first.

This skill enforces the foundational TDD principle: tests drive design, tests come first, and production code exists only to make tests pass.

## When to Use This Skill

Invoke this skill when you need to:
- Start a new feature using TDD methodology
- Enforce proper RED-GREEN-REFACTOR cycle
- Write comprehensive test coverage
- Ensure tests are written before implementation
- Validate TDD workflow compliance
- Refactor code while maintaining test coverage
- Guide team members through TDD process

## The TDD Cycle

### Phase 1: RED - Write Failing Tests

**Objective:** Write comprehensive tests that fail because the functionality doesn't exist yet.

**Steps:**

1. **Understand Requirements**
   - Break down feature into testable behaviors
   - Identify edge cases and error conditions
   - Define expected inputs and outputs

2. **Write Test Cases**
   ```python
   # Example: Testing a non-existent function
   import pytest
   from myapp.feature import calculate_total  # This doesn't exist yet!

   def test_calculate_total_with_valid_items():
       """Should sum item prices correctly."""
       items = [{"price": 10}, {"price": 20}, {"price": 30}]
       assert calculate_total(items) == 60

   def test_calculate_total_with_empty_list():
       """Should return 0 for empty list."""
       assert calculate_total([]) == 0

   def test_calculate_total_with_none():
       """Should raise ValueError for None input."""
       with pytest.raises(ValueError):
           calculate_total(None)
   ```

3. **Run Tests to Confirm Failure**
   ```bash
   pytest tests/test_feature.py -v
   ```

   Expected output:
   ```
   FAILED tests/test_feature.py::test_calculate_total_with_valid_items
   ImportError: cannot import name 'calculate_total'
   ```

4. **Commit Failing Tests**
   ```bash
   git add tests/test_feature.py
   git commit -m "test: add tests for calculate_total function"
   ```

**Quality Checklist for RED Phase:**
- [ ] Tests cover happy path scenarios
- [ ] Tests cover edge cases (empty, None, boundary values)
- [ ] Tests cover error conditions
- [ ] Tests are independent and isolated
- [ ] Tests have clear, descriptive names
- [ ] Tests use proper assertions
- [ ] All tests fail for the right reason (not syntax errors!)
- [ ] Tests are committed before implementation

### Phase 2: GREEN - Minimal Implementation

**Objective:** Write the simplest code possible to make all tests pass.

**Steps:**

1. **Create Minimal Implementation**
   ```python
   # myapp/feature.py
   from typing import List, Dict, Optional

   def calculate_total(items: Optional[List[Dict]]) -> float:
       """Calculate total price of items."""
       if items is None:
           raise ValueError("Items cannot be None")

       if not items:
           return 0

       return sum(item["price"] for item in items)
   ```

2. **Run Tests Iteratively**
   ```bash
   # Run tests after each change
   pytest tests/test_feature.py -v

   # Watch mode for continuous testing
   ptw tests/test_feature.py
   ```

3. **Verify All Tests Pass**
   ```
   PASSED tests/test_feature.py::test_calculate_total_with_valid_items
   PASSED tests/test_feature.py::test_calculate_total_with_empty_list
   PASSED tests/test_feature.py::test_calculate_total_with_none
   ```

4. **Commit Implementation**
   ```bash
   git add myapp/feature.py
   git commit -m "feat: implement calculate_total function"
   ```

**Rules for GREEN Phase:**
- DO NOT modify tests during implementation
- Write simplest code that makes tests pass
- Resist urge to add features not covered by tests
- Focus on making ONE test pass at a time
- Run tests after EVERY change
- Keep implementation minimal and focused

### Phase 3: REFACTOR - Improve Quality

**Objective:** Improve code quality without changing behavior.

**Steps:**

1. **Identify Refactoring Opportunities**
   - Code duplication
   - Long functions (>20 lines)
   - Complex conditionals
   - Missing type hints
   - Poor naming
   - Performance issues

2. **Refactor with Test Safety Net**
   ```python
   # Before refactoring
   def calculate_total(items: Optional[List[Dict]]) -> float:
       if items is None:
           raise ValueError("Items cannot be None")
       if not items:
           return 0
       return sum(item["price"] for item in items)

   # After refactoring
   def calculate_total(items: Optional[List[Dict]]) -> float:
       """
       Calculate total price of items.

       Args:
           items: List of item dictionaries with 'price' key

       Returns:
           Total sum of all item prices

       Raises:
           ValueError: If items is None
       """
       _validate_items(items)
       return _sum_prices(items)

   def _validate_items(items: Optional[List[Dict]]) -> None:
       if items is None:
           raise ValueError("Items cannot be None")

   def _sum_prices(items: List[Dict]) -> float:
       if not items:
           return 0
       return sum(item.get("price", 0) for item in items)
   ```

3. **Run Tests After Each Refactoring**
   ```bash
   pytest tests/test_feature.py -v
   ```

4. **Commit Refactorings**
   ```bash
   git add myapp/feature.py
   git commit -m "refactor: extract validation and calculation helpers"
   ```

**Refactoring Checklist:**
- [ ] All tests still pass
- [ ] Code is more readable
- [ ] Functions are smaller and focused
- [ ] Type hints are complete
- [ ] Docstrings are clear
- [ ] No duplicate code
- [ ] Performance is acceptable
- [ ] Tests still provide same coverage

## Test Quality Standards

### Test Structure (Arrange-Act-Assert)

```python
def test_user_registration():
    # Arrange - Set up test data
    username = "testuser"
    email = "test@example.com"
    password = "SecurePass123!"

    # Act - Perform the action
    user = register_user(username, email, password)

    # Assert - Verify the outcome
    assert user.username == username
    assert user.email == email
    assert user.is_active is True
    assert user.password != password  # Should be hashed
```

### Test Naming Convention

**Pattern:** `test_{function_name}_{scenario}_{expected_outcome}`

**Examples:**
```python
def test_login_with_valid_credentials_returns_user()
def test_login_with_invalid_password_raises_auth_error()
def test_login_with_locked_account_returns_error_message()
def test_calculate_discount_with_negative_amount_raises_value_error()
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_pure_calculation():
    """Fast, isolated unit test."""
    assert add(2, 3) == 5

@pytest.mark.integration
def test_database_query():
    """Test involving database."""
    user = db.get_user(1)
    assert user.name == "Test"

@pytest.mark.asyncio
async def test_async_operation():
    """Async test."""
    result = await fetch_data()
    assert result is not None

@pytest.mark.slow
def test_heavy_operation():
    """Long-running test."""
    process_large_dataset()

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double_value(input, expected):
    """Parametrized test for multiple scenarios."""
    assert double(input) == expected
```

### Coverage Requirements

**Minimum Coverage Targets:**
- Overall: 80%
- Critical paths (orchestrator, github_pr, cli): 95%+
- Utility functions: 90%+
- New features: 100% before merge

**Check Coverage:**
```bash
# Run tests with coverage
pytest --cov=ob1 --cov-report=term-missing

# Generate HTML report
pytest --cov=ob1 --cov-report=html

# Fail if coverage below threshold
pytest --cov=ob1 --cov-fail-under=80
```

## TDD Workflow Automation

### Interactive TDD Prompt Template

Use this template to guide TDD sessions:

```
Phase: {RED|GREEN|REFACTOR}
Feature: {feature description}

Current Task:
{specific task for current phase}

Instructions:
{phase-specific instructions}

Expected Output:
{what should be produced}

Validation:
{how to verify completion}
```

### Phase-Specific Prompts

#### RED Phase Prompt

```
We're using TDD. Write failing tests for {FEATURE} that cover:

1. Happy path: {describe expected normal usage}
2. Edge cases: {list edge cases}
3. Error conditions: {list error scenarios}

Requirements:
- Import functionality that doesn't exist yet
- Use descriptive test names
- Include docstrings
- Use proper assertions
- Cover all scenarios

Don't implement the code yet - just write the tests.
Run pytest to confirm they fail.
Commit with message: "test: add tests for {feature}"
```

#### GREEN Phase Prompt

```
Now implement {MODULE/CLASS} to make all tests pass.

Requirements:
- Write minimal code to pass tests
- Don't modify the tests
- Add complete type hints
- Run tests after each change
- Stop when all tests pass

Iterate until all tests pass.
Commit with message: "feat: implement {feature}"
```

#### REFACTOR Phase Prompt

```
Refactor {MODULE} to improve quality:

Focus areas:
- Extract helper functions
- Add/improve docstrings
- Improve variable names
- Remove duplication
- Enhance type hints

Requirements:
- Run tests after each change
- All tests must still pass
- No behavior changes
- Improve readability

Commit with message: "refactor: improve {component}"
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_feature.py

# Run specific test function
pytest tests/test_feature.py::test_calculate_total

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Quiet mode (less output)
pytest -q
```

### Advanced Test Execution

```bash
# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests in parallel
pytest -n auto

# Watch mode (rerun on file changes)
ptw

# Watch specific directory
ptw tests/unit

# With coverage
pytest --cov=ob1 --cov-report=term-missing

# Generate coverage badge
pytest --cov=ob1 --cov-report=html
coverage-badge -o coverage.svg
```

### Test Configuration

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Fast, isolated unit tests
    integration: Integration tests
    async: Async tests
    slow: Long-running tests
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=ob1
    --cov-report=term-missing
    --cov-fail-under=80
```

## Common TDD Patterns

### Test Fixtures

```python
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_user():
    """Provide sample user for tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "active": True
    }

@pytest.fixture
def mock_database(mocker):
    """Provide mocked database."""
    db = mocker.Mock()
    db.query.return_value = []
    return db

# Use fixtures in tests
def test_user_creation(sample_user):
    user = create_user(**sample_user)
    assert user.username == sample_user["username"]
```

### Mocking and Patching

```python
from unittest.mock import Mock, patch, MagicMock
import pytest

def test_api_call_with_mock(mocker):
    """Test using pytest-mock."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"status": "success"}

    mocker.patch('requests.get', return_value=mock_response)

    result = fetch_data()
    assert result["status"] == "success"

@patch('myapp.external_api.call')
def test_api_call_with_patch(mock_call):
    """Test using unittest.mock.patch."""
    mock_call.return_value = {"data": "test"}

    result = process_external_data()
    assert result == {"data": "test"}
    mock_call.assert_called_once()
```

### Async Testing

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_fetch()
    assert result is not None

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent async operations."""
    results = await asyncio.gather(
        async_operation_1(),
        async_operation_2(),
        async_operation_3()
    )
    assert len(results) == 3
```

## Anti-Patterns to Avoid

### DON'T: Write Tests After Implementation

```python
# WRONG - Implementation first
def calculate_total(items):
    return sum(item["price"] for item in items)

# Then writing tests
def test_calculate_total():
    assert calculate_total([{"price": 10}]) == 10
```

**Why Wrong:** Tests written after are biased by implementation and miss edge cases.

**Do Instead:** Write tests first, thinking about all possible scenarios.

### DON'T: Modify Tests During Implementation

```python
# WRONG - Changing test to match implementation
def test_calculate_total():
    # Original test expected ValueError for None
    # with pytest.raises(ValueError):
    #     calculate_total(None)

    # Changed to match implementation that returns 0
    assert calculate_total(None) == 0
```

**Why Wrong:** Tests should define behavior, not adapt to implementation.

**Do Instead:** If test expectations are wrong, fix in RED phase, commit, then implement.

### DON'T: Skip RED Phase

```python
# WRONG - Writing implementation and tests together
def calculate_total(items):  # Implementation
    return sum(item["price"] for item in items)

def test_calculate_total():  # Test
    assert calculate_total([{"price": 10}]) == 10
```

**Why Wrong:** Never confirmed tests can fail, may have false positives.

**Do Instead:** Write tests, see them fail, then implement.

### DON'T: Add Untested Features

```python
# WRONG - Adding features not covered by tests
def calculate_total(items):
    total = sum(item["price"] for item in items)
    # Added without test
    if total > 1000:
        total *= 0.9  # 10% discount
    return total
```

**Why Wrong:** Untested code will have bugs, defeats TDD purpose.

**Do Instead:** Write test for discount logic first, then implement.

## TDD Enforcement Checklist

Use this checklist to validate TDD compliance:

### Before Starting Feature
- [ ] Feature requirements are clear
- [ ] Test scenarios identified
- [ ] Edge cases documented
- [ ] Error conditions understood
- [ ] Ready to write tests first

### RED Phase Validation
- [ ] Tests written before implementation
- [ ] Tests import non-existent code
- [ ] All test scenarios covered
- [ ] Tests have descriptive names
- [ ] Tests are independent
- [ ] Run pytest and confirmed failures
- [ ] Failures are for correct reasons
- [ ] Tests committed before implementation

### GREEN Phase Validation
- [ ] Implementation makes tests pass
- [ ] No test modifications during implementation
- [ ] Minimal code written (no gold-plating)
- [ ] Tests run after each change
- [ ] All tests now pass
- [ ] Implementation committed separately

### REFACTOR Phase Validation
- [ ] All tests still pass
- [ ] Code quality improved
- [ ] No behavior changes
- [ ] Type hints complete
- [ ] Docstrings added
- [ ] Tests still provide coverage
- [ ] Refactoring committed separately

### Overall Quality
- [ ] Coverage meets minimums (80% overall, 95% critical)
- [ ] All tests have markers
- [ ] No skipped tests without reason
- [ ] No flaky tests
- [ ] Fast test execution (<5 seconds for unit tests)
- [ ] Clear test output on failure

## Integration with ob1 Project

### Project-Specific Configuration

File: `pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
markers =
    unit: Fast, isolated unit tests
    integration: Multi-component tests
    async: Async tests
    slow: Skip in dev
addopts =
    -v
    --tb=short
    --cov=ob1
    --cov-report=term-missing
    --cov-fail-under=80
```

### Test Organization

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── test_config.py
│   ├── test_logger.py
│   └── test_utils.py
├── integration/          # Multi-component tests
│   ├── test_orchestrator.py
│   ├── test_workflow.py
│   └── test_pr_creation.py
├── fixtures/             # Shared test data
│   ├── sample_repos/
│   └── mock_responses/
├── conftest.py          # Shared fixtures
└── __init__.py
```

### Example TDD Session for ob1

**Feature:** Add GitHub PR description generation

**RED Phase:**
```python
# tests/unit/test_pr_description.py
import pytest
from ob1.workspace.pr_description import generate_pr_description

def test_generate_pr_description_with_commits():
    """Should generate description from commit messages."""
    commits = [
        {"message": "feat: add user login"},
        {"message": "test: add login tests"},
        {"message": "fix: handle empty password"}
    ]

    description = generate_pr_description(commits)

    assert "user login" in description.lower()
    assert len(description) > 50
    assert description.startswith("## Summary")

def test_generate_pr_description_empty_commits():
    """Should return default for empty commits."""
    description = generate_pr_description([])
    assert description == "## Summary\n\nNo commits provided."

@pytest.mark.asyncio
async def test_generate_pr_description_with_diff():
    """Should include test plan from diff analysis."""
    commits = [{"message": "feat: add API endpoint"}]
    diff = "+def get_users():\n+    return db.query(User)"

    description = await generate_pr_description(commits, diff=diff)

    assert "## Test Plan" in description
    assert "API endpoint" in description
```

Run: `pytest tests/unit/test_pr_description.py -v` (should fail)

Commit: `git commit -m "test: add tests for PR description generation"`

**GREEN Phase:**
```python
# ob1/workspace/pr_description.py
from typing import List, Dict, Optional

def generate_pr_description(
    commits: List[Dict[str, str]],
    diff: Optional[str] = None
) -> str:
    """Generate PR description from commits and diff."""
    if not commits:
        return "## Summary\n\nNo commits provided."

    summary = _extract_summary(commits)
    description = f"## Summary\n\n{summary}"

    if diff:
        description += "\n\n## Test Plan\n\n- Manual testing required"

    return description

def _extract_summary(commits: List[Dict[str, str]]) -> str:
    messages = [c["message"] for c in commits]
    return " ".join(messages)
```

Run: `pytest tests/unit/test_pr_description.py -v` (should pass)

Commit: `git commit -m "feat: implement PR description generation"`

**REFACTOR Phase:**
```python
# ob1/workspace/pr_description.py
from typing import List, Dict, Optional
import re

def generate_pr_description(
    commits: List[Dict[str, str]],
    diff: Optional[str] = None
) -> str:
    """
    Generate PR description from commits and optional diff.

    Args:
        commits: List of commit dictionaries with 'message' key
        diff: Optional diff content for test plan generation

    Returns:
        Formatted PR description with summary and test plan
    """
    if not commits:
        return _default_description()

    summary = _extract_summary(commits)
    test_plan = _generate_test_plan(diff) if diff else None

    return _format_description(summary, test_plan)

def _default_description() -> str:
    return "## Summary\n\nNo commits provided."

def _extract_summary(commits: List[Dict[str, str]]) -> str:
    """Extract and format summary from commit messages."""
    messages = [_clean_commit_message(c["message"]) for c in commits]
    return " ".join(messages)

def _clean_commit_message(message: str) -> str:
    """Remove conventional commit prefixes."""
    return re.sub(r'^(feat|fix|test|refactor):\s*', '', message)

def _generate_test_plan(diff: str) -> str:
    """Generate test plan from diff content."""
    # Simple implementation for now
    return "- Manual testing required"

def _format_description(summary: str, test_plan: Optional[str]) -> str:
    """Format final PR description."""
    parts = [f"## Summary\n\n{summary}"]

    if test_plan:
        parts.append(f"## Test Plan\n\n{test_plan}")

    return "\n\n".join(parts)
```

Run: `pytest tests/unit/test_pr_description.py -v` (should still pass)

Commit: `git commit -m "refactor: improve PR description generation structure"`

## Quick Reference

### TDD Commands

```bash
# Start TDD session
pytest tests/test_new_feature.py -v  # Should fail

# Implement and test iteratively
ptw tests/test_new_feature.py  # Watch mode

# Verify all pass
pytest tests/test_new_feature.py -v

# Check coverage
pytest --cov=ob1 --cov-report=term-missing

# Run full test suite
pytest -n auto
```

### Phase Checklist

**RED:**
1. Write tests
2. Run and confirm failure
3. Commit tests

**GREEN:**
1. Implement minimally
2. Run tests iteratively
3. Commit when passing

**REFACTOR:**
1. Improve quality
2. Run tests after each change
3. Commit improvements

### Common Mistakes

- Writing code before tests (violates TDD)
- Modifying tests to match implementation (tests should be stable)
- Adding features without tests (defeats purpose)
- Skipping RED phase (never know if tests can fail)
- Not running tests frequently (lose fast feedback)

## Additional Resources

- ob1 TDD Philosophy: `/CLAUDE.md`
- Test Configuration: `/pytest.ini`
- Test Fixtures: `/tests/conftest.py`
- Example Tests: `/tests/unit/`, `/tests/integration/`
- Pytest Documentation: https://docs.pytest.org/

---

**Remember:** Tests first, always. The RED-GREEN-REFACTOR cycle is not optional—it's the foundation of reliable software development.
