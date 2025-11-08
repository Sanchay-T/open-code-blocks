---
description: Run complete RED-GREEN-REFACTOR TDD cycle for a feature
argument-hints:
  - feature_name: Name of the feature (e.g., "parallel agent orchestration")
  - module_path: Module path (e.g., "agents/claude", "workspace/worktree")
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(pytest*)
  - Bash(mypy*)
  - Bash(black*)
  - Bash(git*)
---

# Complete TDD Cycle: RED-GREEN-REFACTOR

You are running a complete Test-Driven Development cycle from start to finish.

## The Mission

Implement **{feature_name}** following strict TDD methodology:
1. RED: Write failing tests
2. GREEN: Make tests pass
3. REFACTOR: Improve code quality

## Overview: The TDD Cycle

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌─────────┐      ┌─────────┐      ┌──────────┐   │
│  │   RED   │ ───> │  GREEN  │ ───> │ REFACTOR │   │
│  └─────────┘      └─────────┘      └──────────┘   │
│       │                                    │        │
│       │                                    │        │
│       └────────────────────────────────────┘        │
│              (Next Feature)                         │
│                                                     │
└─────────────────────────────────────────────────────┘

RED:      Write tests first (they fail)
GREEN:    Implement code (tests pass)
REFACTOR: Improve quality (tests stay green)
REPEAT:   Next feature/enhancement
```

## Prerequisites

Before starting, ensure:

```bash
cd /Users/sanchay/Documents/open-code-blocks

# Project setup complete
ls ob1/ tests/

# Dependencies installed
pip list | grep pytest

# Git clean state
git status

# Review project guidelines
cat CLAUDE.md
```

## Phase 1: RED - Write Failing Tests

**Objective:** Create comprehensive tests that define the feature's behavior.

### Step 1.1: Analyze Requirements

- What problem does this feature solve?
- What is the public API (classes, functions, methods)?
- What are the inputs and outputs?
- What are the edge cases?
- What are the error conditions?

### Step 1.2: Design Test Structure

Determine:
- Test file location: `tests/unit/` or `tests/integration/`
- Test class name: `Test{ClassName}`
- Test methods covering:
  - Happy path scenarios
  - Edge cases
  - Error conditions
  - Async operations
  - Integration points

### Step 1.3: Write Comprehensive Tests

Create test file for module at `ob1/{module_path}`:

```python
# tests/unit/test_{module_name}.py

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

# Import functionality that DOESN'T EXIST YET
from ob1.{module_path} import {ClassName}, {FunctionName}


@pytest.mark.unit
class Test{ClassName}:
    """Comprehensive test suite for {ClassName}."""

    # HAPPY PATH TESTS

    def test_initialization_with_valid_params(self):
        """Test successful initialization with valid parameters."""
        # Arrange
        param1 = "valid_value"

        # Act
        instance = {ClassName}(param1)

        # Assert
        assert instance.param1 == param1

    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test successful async operation."""
        # Arrange
        instance = {ClassName}("test")

        # Act
        result = await instance.perform_operation()

        # Assert
        assert result is not None
        assert result.status == "success"

    # EDGE CASES

    def test_empty_input_handling(self):
        """Test handling of empty input."""
        instance = {ClassName}("")
        result = instance.process()
        assert result == []

    def test_maximum_limit_handling(self):
        """Test handling of maximum allowed values."""
        instance = {ClassName}("test")
        large_input = ["item"] * 1000
        result = instance.process(large_input)
        assert len(result) <= 1000

    # ERROR CASES

    def test_invalid_input_raises_value_error(self):
        """Test that invalid input raises ValueError."""
        with pytest.raises(ValueError, match="Invalid input"):
            {ClassName}(invalid_param)

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test graceful handling of network errors."""
        instance = {ClassName}("test")

        with patch('httpx.AsyncClient.get', side_effect=NetworkError()):
            with pytest.raises(NetworkError):
                await instance.fetch_data()

    # INTEGRATION/MOCK TESTS

    @pytest.mark.asyncio
    async def test_integration_with_dependency(self):
        """Test integration with external dependency."""
        mock_dependency = AsyncMock()
        mock_dependency.do_something.return_value = "expected"

        instance = {ClassName}(dependency=mock_dependency)
        result = await instance.use_dependency()

        assert result == "expected"
        mock_dependency.do_something.assert_called_once()


@pytest.mark.unit
def test_standalone_function():
    """Test standalone utility function."""
    result = {FunctionName}("input")
    assert result == "expected_output"
```

### Step 1.4: Run Tests - Confirm RED

```bash
cd /Users/sanchay/Documents/open-code-blocks

# Run new tests (should ALL fail)
pytest tests/unit/test_{module_name}.py -v

# Expected output:
# ImportError: cannot import name '{ClassName}'
# or
# ModuleNotFoundError: No module named 'ob1.{module_path}'
```

**SUCCESS CRITERION:** All tests fail because production code doesn't exist.

### Step 1.5: Commit Failing Tests

```bash
cd /Users/sanchay/Documents/open-code-blocks

git add tests/unit/test_{module_name}.py
git commit -m "test: add comprehensive tests for {feature_name}

- Add happy path tests for core functionality
- Add edge case handling tests
- Add error condition tests
- Add integration tests with mocks
- All tests currently FAILING (RED phase)

Module: ob1/{module_path}
Coverage areas:
- {Test area 1}
- {Test area 2}
- {Test area 3}

TDD Phase: RED ✓"
```

## Phase 2: GREEN - Implement to Pass Tests

**Objective:** Write minimal code to make all tests pass.

### Step 2.1: Create Module Structure

```bash
cd /Users/sanchay/Documents/open-code-blocks

# Create module directory if needed
mkdir -p ob1/{module_path}

# Create __init__.py if needed
touch ob1/{module_path}/__init__.py
```

### Step 2.2: Implement Minimal Code

Create `ob1/{module_path}/{module_name}.py`:

```python
"""
{Feature name} implementation.

This module provides {brief description of what it does}.
"""

from typing import Optional, List, Dict, Any, Protocol
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)


class {ClassName}:
    """
    {One-line description}.

    {Detailed description of the class purpose and behavior.}

    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2

    Example:
        >>> instance = {ClassName}("param")
        >>> result = await instance.perform_operation()
        >>> print(result)
    """

    def __init__(
        self,
        param1: str,
        dependency: Optional[DependencyType] = None
    ) -> None:
        """
        Initialize {ClassName}.

        Args:
            param1: Description of param1
            dependency: Optional dependency injection

        Raises:
            ValueError: If param1 is invalid
        """
        if not param1:
            raise ValueError("param1 cannot be empty")

        self._param1 = param1
        self._dependency = dependency or DefaultDependency()

    async def perform_operation(self) -> Result:
        """
        Perform the main operation.

        Returns:
            Result object with operation outcome

        Raises:
            NetworkError: If network operation fails
        """
        logger.info(f"Performing operation for {self._param1}")

        try:
            data = await self._dependency.fetch_data()
            return self._process_data(data)
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise

    def _process_data(self, data: Any) -> Result:
        """Process raw data into result (private helper)."""
        # Simple processing logic
        return Result(status="success", data=data)


def standalone_function(input_value: str) -> str:
    """
    Standalone utility function.

    Args:
        input_value: Input string to process

    Returns:
        Processed string
    """
    return input_value.upper()
```

### Step 2.3: Iterative Test-Driven Implementation

**REPEAT THIS LOOP:**

```bash
# 1. Run tests
pytest tests/unit/test_{module_name}.py -v

# 2. Observe which test is failing

# 3. Make SMALLEST possible change to pass that test

# 4. Run tests again
pytest tests/unit/test_{module_name}.py -v

# 5. If all pass, continue to next step
# 6. If some fail, repeat from step 2
```

### Step 2.4: Verify All Tests Pass

```bash
cd /Users/sanchay/Documents/open-code-blocks

# All new tests pass
pytest tests/unit/test_{module_name}.py -v

# No regressions in other tests
pytest tests/unit/ -v

# Check coverage
pytest tests/unit/test_{module_name}.py --cov=ob1.{module_path} --cov-report=term-missing
```

**SUCCESS CRITERION:** 100% of tests passing, coverage > 80%

### Step 2.5: Commit Implementation

```bash
cd /Users/sanchay/Documents/open-code-blocks

git add ob1/{module_path}/
git commit -m "feat: implement {feature_name}

- Create {ClassName} with full functionality
- Implement all required methods
- Add complete type hints
- Use async/await for I/O operations
- All tests PASSING (GREEN phase)
- Coverage: {XX}%

Module: ob1/{module_path}
Tests: {X} passing

TDD Phase: GREEN ✓"
```

## Phase 3: REFACTOR - Improve Quality

**Objective:** Enhance code quality while keeping tests green.

### Step 3.1: Identify Refactoring Opportunities

Review code for:
- [ ] Incomplete type hints
- [ ] Missing docstrings
- [ ] Complex functions (> 20 lines)
- [ ] Magic numbers
- [ ] Poor variable names
- [ ] Duplicated code
- [ ] Files > 300 lines

### Step 3.2: Incremental Refactoring

**FOR EACH IMPROVEMENT:**

```bash
# 1. Make ONE small change (e.g., rename variable)

# 2. Run tests IMMEDIATELY
pytest tests/unit/test_{module_name}.py -v

# 3. If tests pass, continue
# 4. If tests fail, REVERT and try smaller change

# 5. Commit the improvement
git add ob1/{module_path}/
git commit -m "refactor: improve {specific aspect}"
```

### Step 3.3: Common Refactorings

#### Add Complete Type Hints
```python
# Run mypy to find missing hints
mypy ob1/{module_path}

# Add hints throughout
from typing import Optional, List, Dict, Any, Union, Callable
```

#### Extract Helper Methods
```python
# If method > 20 lines, extract to helpers
def complex_method(self):
    # 50 lines of logic

# BECOMES:
def complex_method(self) -> Result:
    step1_result = self._perform_step1()
    step2_result = self._perform_step2(step1_result)
    return self._finalize(step2_result)
```

#### Improve Names
```python
# Generic names
def process(self, d):
    r = d['value']

# Descriptive names
def extract_value(self, data: Dict[str, Any]) -> str:
    extracted_value = data['value']
```

#### Extract Constants
```python
# Magic numbers
if count > 100:

# Named constants
MAX_ITEMS = 100
if count > MAX_ITEMS:
```

### Step 3.4: Run Full Quality Checks

```bash
cd /Users/sanchay/Documents/open-code-blocks

# All tests pass
pytest tests/ -v

# Coverage maintained
pytest --cov=ob1 --cov-report=term-missing --cov-fail-under=80

# Type checking
mypy ob1/{module_path}

# Formatting
black ob1/{module_path} tests/

# Linting
flake8 ob1/{module_path}
```

### Step 3.5: Final Refactor Commit

```bash
cd /Users/sanchay/Documents/open-code-blocks

git add ob1/{module_path}/
git commit -m "refactor: improve code quality in {feature_name}

- Add complete type hints
- Extract helper methods for complex logic
- Improve variable and method naming
- Add comprehensive docstrings
- Extract magic numbers to named constants
- All tests remain PASSING
- Coverage maintained: {XX}%

TDD Phase: REFACTOR ✓

Complete TDD cycle: RED → GREEN → REFACTOR ✓✓✓"
```

## Success Criteria - Full Cycle

- [ ] **RED Phase Complete**
  - [ ] Comprehensive tests written
  - [ ] Tests initially failed
  - [ ] Tests committed

- [ ] **GREEN Phase Complete**
  - [ ] All tests passing
  - [ ] Minimal implementation
  - [ ] Implementation committed

- [ ] **REFACTOR Phase Complete**
  - [ ] Code quality improved
  - [ ] Tests still passing
  - [ ] Improvements committed

- [ ] **Quality Standards Met**
  - [ ] Type hints complete
  - [ ] Docstrings on all public APIs
  - [ ] Coverage > 80% (95%+ for critical paths)
  - [ ] mypy passes
  - [ ] black formatting applied
  - [ ] No files > 300 lines

## Summary Output

After completing full cycle, summarize:

```
✓ TDD CYCLE COMPLETE: {feature_name}

Module: ob1/{module_path}

RED Phase:
- Tests written: {X}
- Initial failures: {X} (expected)
- Commit: {commit_sha}

GREEN Phase:
- Tests passing: {X}/{X}
- Coverage: {XX}%
- Commit: {commit_sha}

REFACTOR Phase:
- Improvements: {list key improvements}
- Tests passing: {X}/{X}
- Final coverage: {XX}%
- Commit: {commit_sha}

Quality Checks:
- pytest: ✓ All passing
- mypy: ✓ No errors
- black: ✓ Formatted
- coverage: ✓ {XX}%

Ready for: Code review / Next feature
```

## What NOT to Do

- **DON'T** skip the RED phase (writing tests first)
- **DON'T** modify tests during GREEN phase
- **DON'T** add features during REFACTOR phase
- **DON'T** commit if tests are failing
- **DON'T** make multiple changes before running tests
- **DON'T** skip type hints or docstrings

## Next Steps

After completing TDD cycle:
1. Start another cycle for next feature: `/tdd-cycle {next_feature}`
2. Or run individual phases for small changes:
   - `/tdd-red` for new feature tests
   - `/tdd-green` to implement
   - `/tdd-refactor` to improve

---

**Remember:** TDD is a discipline. Each phase has a purpose:
- **RED**: Think about WHAT the code should do
- **GREEN**: Make it WORK
- **REFACTOR**: Make it BETTER

**The cycle creates high-quality, well-tested code. Trust the process!**
