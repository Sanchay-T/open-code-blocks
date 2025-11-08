---
description: Implement code to make failing tests pass (TDD GREEN phase)
argument-hints:
  - feature_name: Name of the feature being implemented
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(pytest*)
  - Bash(git*)
---

# TDD GREEN Phase: Make Tests Pass

You are in the **GREEN** phase of the Test-Driven Development cycle.

## Your Mission

Implement minimal code to make all failing tests pass for: **{feature_name}**

## The Sacred Rules

1. **DO NOT modify the tests** - they define the contract
2. **Implement only enough** to make tests pass
3. **Run tests frequently** - after every small change
4. **Keep it simple** - refactoring comes later

## Step-by-Step Process

### 1. Review the Failing Tests

Read the test file(s) to understand:
- What classes/functions need to be created
- Expected method signatures
- Expected behavior and return values
- Error conditions and exceptions

```bash
cd /Users/sanchay/Documents/open-code-blocks
# Review the tests
cat tests/unit/test_{module_name}.py
# Or grep for specific test patterns
grep -n "def test_" tests/unit/test_{module_name}.py
```

### 2. Create Minimal Implementation

Start with the simplest possible implementation:

```python
# ob1/{module_path}/{module_name}.py

"""
{Module description}

This module implements {feature_name}.
"""

from typing import Optional, List, Dict, Any
import asyncio


class {ClassName}:
    """
    {Class description}

    This class handles {responsibility}.
    """

    def __init__(self, dependency: DependencyType) -> None:
        """
        Initialize {ClassName}.

        Args:
            dependency: Description of dependency
        """
        self._dependency = dependency

    async def method_name(self, param: str) -> ResultType:
        """
        Method description.

        Args:
            param: Parameter description

        Returns:
            Description of return value

        Raises:
            ValueError: When invalid input provided
        """
        # Minimal implementation to pass tests
        if not param:
            raise ValueError("param cannot be empty")

        # Simple logic to satisfy tests
        result = await self._dependency.do_something(param)
        return result
```

### 3. Iterative Development Cycle

**DO THIS REPEATEDLY:**

#### A. Run Tests
```bash
cd /Users/sanchay/Documents/open-code-blocks
pytest tests/unit/test_{module_name}.py -v
```

#### B. Read Test Output
- How many tests passing?
- Which test is currently failing?
- What's the error message?

#### C. Make Smallest Change
- Add one method/function
- Fix one failing assertion
- Handle one error case

#### D. Run Tests Again
```bash
pytest tests/unit/test_{module_name}.py -v --tb=short
```

#### E. Repeat Until All Green

### 4. Implementation Checklist

As you implement, ensure:

- [ ] **Type Hints**: All parameters and return types annotated
- [ ] **Docstrings**: Google-style docstrings for all public functions/classes
- [ ] **Async/Await**: All I/O operations are async
- [ ] **Error Handling**: Proper exception raising/catching
- [ ] **Dependencies**: Injected via constructor, not hardcoded
- [ ] **File Size**: Keep under 300 lines (extract if needed)
- [ ] **Single Responsibility**: Each class/function does one thing

### 5. Code Quality Standards

#### Type Hints (MANDATORY)
```python
from typing import Optional, List, Dict, Any, Protocol
from pathlib import Path

async def create_worktree(
    repo_path: Path,
    branch_name: str,
    base_branch: str = "main"
) -> Path:
    """Create a new git worktree."""
    ...
```

#### Async for I/O (MANDATORY)
```python
import asyncio
import httpx

async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async def run_command(cmd: List[str]) -> str:
    """Run shell command asynchronously."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode()
```

#### Dependency Injection
```python
class Orchestrator:
    """Orchestrate parallel agent execution."""

    def __init__(
        self,
        agent_factory: AgentFactory,
        workspace_manager: WorkspaceManager,
        github_client: GitHubClient
    ) -> None:
        """Initialize with dependencies."""
        self._agent_factory = agent_factory
        self._workspace_manager = workspace_manager
        self._github_client = github_client
```

### 6. Running Tests - Multiple Modes

```bash
# Single test file
pytest tests/unit/test_{module_name}.py -v

# Specific test
pytest tests/unit/test_{module_name}.py::test_specific_function -v

# With detailed output
pytest tests/unit/test_{module_name}.py -vv --tb=long

# Stop on first failure
pytest tests/unit/test_{module_name}.py -x

# Show print statements
pytest tests/unit/test_{module_name}.py -s

# Run only failed tests from last run
pytest --lf

# Coverage for this module
pytest tests/unit/test_{module_name}.py --cov=ob1.{module_path} --cov-report=term-missing
```

### 7. When All Tests Pass

Verify complete success:

```bash
cd /Users/sanchay/Documents/open-code-blocks

# Run all tests for this module
pytest tests/unit/test_{module_name}.py -v

# Check coverage
pytest tests/unit/test_{module_name}.py --cov=ob1.{module_path} --cov-report=term-missing

# Ensure no regressions in other tests
pytest tests/unit/ -v
```

### 8. Commit the Implementation

Once ALL tests pass:

```bash
cd /Users/sanchay/Documents/open-code-blocks

git add ob1/{module_path}/
git commit -m "feat: implement {feature_name}

- Create {ClassName} with full functionality
- All tests passing (GREEN phase)
- Type hints and async/await implemented
- Coverage: {XX}%

TDD GREEN phase complete. Ready for REFACTOR."
```

## What NOT to Do

- **DON'T** modify the tests to make them pass
- **DON'T** skip running tests frequently
- **DON'T** add features not required by tests
- **DON'T** optimize prematurely (that's for REFACTOR phase)
- **DON'T** commit if tests are failing
- **DON_T** forget type hints or docstrings

## Debugging Failed Tests

If stuck on a failing test:

1. **Read the test carefully** - what is it asserting?
2. **Check the error message** - what specifically failed?
3. **Add print/log statements** - understand what's happening
4. **Use pytest -s** - see your debug output
5. **Check test fixtures** - are mocks configured correctly?
6. **Verify imports** - is everything imported properly?

## Success Criteria

- [ ] All tests passing (100% green)
- [ ] No tests modified during implementation
- [ ] Type hints on all functions/methods
- [ ] Docstrings on all public APIs
- [ ] Async/await used for I/O operations
- [ ] Dependencies injected, not hardcoded
- [ ] Files under 300 lines
- [ ] Code committed with `feat:` prefix

## Next Steps

After GREEN phase complete:
1. Run `/tdd-refactor` to improve code quality
2. Or run `/tdd-red` to add more test coverage for additional features

---

**Remember:** GREEN phase is about making tests pass with simple, direct code. Don't get fancy - that's what REFACTOR is for.

**When in doubt, ask: "Is this the simplest thing that could possibly work?" If yes, ship it and refactor later.**
