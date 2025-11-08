---
description: Start TDD RED phase by writing failing tests for a feature
argument-hints:
  - feature_name: Name of the feature to test (e.g., "worktree manager", "PR creation")
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash(pytest*)
  - Bash(git*)
---

# TDD RED Phase: Write Failing Tests First

You are starting the **RED** phase of the Test-Driven Development cycle.

## The Golden Rule

**NEVER write production code without a failing test first.**

## Your Mission

Write comprehensive failing tests for: **{feature_name}**

## Step-by-Step Process

### 1. Understand the Feature Requirements

- Read `/Users/sanchay/Documents/open-code-blocks/CLAUDE.md` to understand project standards
- Identify the module/class that will implement this feature
- Determine the expected API and behavior
- Consider edge cases and error conditions

### 2. Write Comprehensive Test Cases

Create tests that cover:

#### Happy Path Tests
- Primary use cases
- Expected inputs and outputs
- Successful operation scenarios

#### Edge Cases
- Boundary conditions
- Empty/null inputs
- Maximum/minimum values
- Unusual but valid inputs

#### Error Cases
- Invalid inputs
- Expected exceptions
- Failure scenarios
- Error messages

#### Integration Points
- Dependencies (mock them appropriately)
- External services
- File system operations
- Network calls

### 3. Test File Organization

```python
# tests/unit/test_{module_name}.py or tests/integration/test_{module_name}.py

import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import the functionality that DOESN'T EXIST YET
from ob1.{module_path} import {ClassName}


@pytest.mark.unit  # or @pytest.mark.integration
class Test{ClassName}:
    """Test suite for {ClassName}."""

    def test_basic_functionality(self):
        """Test basic happy path."""
        # Arrange
        ...

        # Act
        result = ...

        # Assert
        assert result == expected

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async operations."""
        ...

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ExpectedException):
            ...
```

### 4. Testing Standards (from CLAUDE.md)

- Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.async`
- Follow AAA pattern: Arrange, Act, Assert
- Use descriptive test names: `test_feature_when_condition_then_behavior`
- Mock external dependencies
- Test one thing per test function
- Include docstrings explaining what each test validates

### 5. Run Tests to Confirm Failure (RED)

Execute:
```bash
cd /Users/sanchay/Documents/open-code-blocks
pytest tests/ -v -k {feature_name}
```

**Expected outcome:** All tests should FAIL because the production code doesn't exist yet.

Look for errors like:
- `ImportError: cannot import name '{ClassName}'`
- `ModuleNotFoundError: No module named 'ob1.{module}'`
- `AttributeError: module has no attribute '{function}'`

These failures are GOOD - they confirm we're testing functionality that doesn't exist yet.

### 6. Commit the Failing Tests

Once tests are written and confirmed failing:

```bash
cd /Users/sanchay/Documents/open-code-blocks
git add tests/
git commit -m "test: add tests for {feature_name}

- Add comprehensive test coverage for {feature_name}
- Cover happy path, edge cases, and error conditions
- Tests currently failing (RED phase) - ready for implementation

TDD RED phase complete."
```

## Success Criteria

- [ ] Tests written for all major use cases
- [ ] Edge cases and error conditions covered
- [ ] Tests use appropriate pytest markers
- [ ] All tests currently FAIL (this is correct!)
- [ ] Import statements reference non-existent production code
- [ ] Tests committed to git with `test:` prefix

## What NOT to Do

- **DON'T** write any production code yet
- **DON'T** create the module files being imported
- **DON'T** worry about tests passing (they should fail!)
- **DON'T** skip edge cases or error testing
- **DON'T** write tests after implementation

## Next Steps

After completing RED phase and committing:
1. Run `/tdd-green` to implement the code
2. Or continue with more tests if coverage is incomplete

## Type Hints Reminder

All test fixtures and helper functions should have type hints:

```python
from typing import AsyncGenerator
import pytest

@pytest.fixture
async def mock_client() -> AsyncGenerator[MockClient, None]:
    """Provide a mock HTTP client."""
    client = MockClient()
    yield client
    await client.close()
```

## Coverage Target

Aim for 95%+ coverage on critical paths (orchestrator, github_pr, cli).

---

**Remember:** The RED phase is about thoughtful test design. Take time to consider what SHOULD happen before writing code that makes it happen.

**When in doubt, ask: "Have I tested enough scenarios?" The answer is usually "Add one more edge case test."**
