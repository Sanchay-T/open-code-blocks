---
description: Refactor code while keeping tests green (TDD REFACTOR phase)
argument-hints:
  - module_name: Module to refactor (e.g., "orchestrator", "github_pr")
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash(pytest*)
  - Bash(mypy*)
  - Bash(black*)
  - Bash(git*)
---

# TDD REFACTOR Phase: Improve Code Quality

You are in the **REFACTOR** phase of the Test-Driven Development cycle.

## Your Mission

Improve the code quality of **{module_name}** while keeping all tests green.

## The Golden Rule

**Tests must remain GREEN throughout refactoring. Run tests after EVERY change.**

## Step-by-Step Process

### 1. Verify Starting State

Before refactoring, ensure:

```bash
cd /Users/sanchay/Documents/open-code-blocks

# All tests passing
pytest tests/ -v

# Check current coverage
pytest --cov=ob1.{module_name} --cov-report=term-missing

# Type checking baseline
mypy ob1/{module_name}

# Code formatting baseline
black --check ob1/{module_name}
```

**DO NOT PROCEED** if any tests are failing!

### 2. Refactoring Targets

Focus on these improvements:

#### A. Type Hint Completeness

**Check for missing type hints:**

```python
# BEFORE (incomplete)
def process_data(data):
    return data.upper()

# AFTER (complete)
def process_data(data: str) -> str:
    """Process data by converting to uppercase."""
    return data.upper()
```

**Complex type hints:**
```python
from typing import Optional, List, Dict, Any, Union, Callable, Protocol, TypeVar
from pathlib import Path

T = TypeVar('T')

async def fetch_items(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    validator: Optional[Callable[[Dict[str, Any]], bool]] = None
) -> List[Dict[str, Any]]:
    """Fetch and validate items from API."""
    ...
```

#### B. Code Structure Improvements

**Extract magic numbers to constants:**
```python
# BEFORE
if len(agents) > 5:
    raise ValueError("Too many agents")

# AFTER
MAX_CONCURRENT_AGENTS = 5

if len(agents) > MAX_CONCURRENT_AGENTS:
    raise ValueError(f"Cannot exceed {MAX_CONCURRENT_AGENTS} concurrent agents")
```

**Extract complex logic to helper functions:**
```python
# BEFORE
def process(self, items):
    result = []
    for item in items:
        if item['status'] == 'active' and item['priority'] > 5:
            result.append({
                'id': item['id'],
                'name': item['name'].upper(),
                'score': item['priority'] * 2
            })
    return result

# AFTER
def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process items, filtering and transforming active high-priority items."""
    active_items = self._filter_active_high_priority(items)
    return [self._transform_item(item) for item in active_items]

def _filter_active_high_priority(
    self,
    items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Filter for active items with priority > 5."""
    return [
        item for item in items
        if item['status'] == 'active' and item['priority'] > 5
    ]

def _transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    """Transform item to output format."""
    return {
        'id': item['id'],
        'name': item['name'].upper(),
        'score': item['priority'] * 2
    }
```

#### C. Naming Improvements

**Use descriptive variable names:**
```python
# BEFORE
def calc(a, b, c):
    r = a * b / c
    return r

# AFTER
def calculate_weighted_average(
    total_value: float,
    weight: float,
    divisor: float
) -> float:
    """Calculate weighted average value."""
    weighted_average = total_value * weight / divisor
    return weighted_average
```

**Use verb-noun method names:**
```python
# BEFORE
class WorktreeManager:
    def worktree(self, name): ...
    def cleanup(self): ...

# AFTER
class WorktreeManager:
    def create_worktree(self, branch_name: str) -> Path: ...
    def remove_worktree(self, worktree_path: Path) -> None: ...
    def cleanup_stale_worktrees(self) -> List[Path]: ...
```

#### D. Error Handling Improvements

**Specific exceptions:**
```python
# BEFORE
def parse_config(path):
    if not path.exists():
        raise Exception("File not found")
    return load(path)

# AFTER
class ConfigError(Exception):
    """Configuration related errors."""
    pass

def parse_config(path: Path) -> Config:
    """
    Parse configuration from file.

    Args:
        path: Path to configuration file

    Returns:
        Parsed configuration object

    Raises:
        ConfigError: If file doesn't exist or is invalid
    """
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        return load(path)
    except ValueError as e:
        raise ConfigError(f"Invalid configuration format: {e}") from e
```

#### E. Documentation Improvements

**Complete docstrings:**
```python
class AgentOrchestrator:
    """
    Orchestrate parallel execution of multiple AI agents.

    This class manages the creation, execution, and coordination of multiple
    AI agents working on the same task in parallel. Each agent works in an
    isolated git worktree and produces a separate pull request.

    Attributes:
        max_agents: Maximum number of concurrent agents
        workspace_dir: Directory for agent worktrees

    Example:
        >>> orchestrator = AgentOrchestrator(max_agents=3)
        >>> await orchestrator.run_parallel_task("implement feature X")
    """

    def __init__(
        self,
        max_agents: int = 3,
        workspace_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize the orchestrator.

        Args:
            max_agents: Maximum concurrent agents (default: 3)
            workspace_dir: Directory for worktrees (default: ./.ob1-workspace)

        Raises:
            ValueError: If max_agents < 1 or > 10
        """
        ...
```

#### F. Code Organization

**File size check:**
```bash
wc -l ob1/{module_name}/*.py
```

If any file > 300 lines, extract to separate modules:

```python
# BEFORE: orchestrator.py (450 lines)
class Orchestrator:
    # 200 lines of orchestration logic
    # 150 lines of worktree management
    # 100 lines of PR creation

# AFTER: Split into focused modules
# orchestrator.py (200 lines) - core orchestration
# worktree_manager.py (150 lines) - worktree operations
# pr_creator.py (100 lines) - PR creation
```

### 3. The Refactoring Loop

**REPEAT THIS CYCLE:**

#### A. Make One Small Change
- Improve one function name
- Add type hints to one function
- Extract one helper method
- Improve one docstring

#### B. Run Tests Immediately
```bash
cd /Users/sanchay/Documents/open-code-blocks
pytest tests/unit/test_{module_name}.py -v
```

#### C. If Tests Fail
- **REVERT IMMEDIATELY** - don't try to fix forward
- Understand why the change broke tests
- Make a smaller, safer change

#### D. If Tests Pass
- Run additional checks:
```bash
# Type checking
mypy ob1/{module_name}

# Formatting
black ob1/{module_name} tests/

# All tests (catch regressions)
pytest tests/ -v
```

#### E. Commit Frequently
```bash
git add ob1/{module_name}
git commit -m "refactor: improve {specific_aspect} in {module_name}

- {What you changed}
- All tests still passing"
```

### 4. Quality Checks

Run these after refactoring:

```bash
cd /Users/sanchay/Documents/open-code-blocks

# All tests pass
pytest tests/ -v

# High coverage maintained
pytest --cov=ob1.{module_name} --cov-report=term-missing --cov-fail-under=80

# Type checking passes
mypy ob1/{module_name}

# Code formatted
black ob1/{module_name} tests/

# Linting passes
flake8 ob1/{module_name} --max-line-length=100
```

### 5. Common Refactoring Patterns

#### Extract Method
```python
# BEFORE
def process_request(self, request):
    # Validate
    if not request.user_id:
        raise ValueError("Missing user_id")
    if not request.action:
        raise ValueError("Missing action")

    # Execute
    user = self.db.get_user(request.user_id)
    result = user.perform(request.action)

    # Log
    self.logger.info(f"User {user.id} performed {request.action}")

    return result

# AFTER
def process_request(self, request: Request) -> Result:
    """Process user request."""
    self._validate_request(request)
    result = self._execute_action(request)
    self._log_action(request, result)
    return result

def _validate_request(self, request: Request) -> None:
    """Validate request has required fields."""
    if not request.user_id:
        raise ValueError("Missing user_id")
    if not request.action:
        raise ValueError("Missing action")

def _execute_action(self, request: Request) -> Result:
    """Execute the requested action."""
    user = self.db.get_user(request.user_id)
    return user.perform(request.action)

def _log_action(self, request: Request, result: Result) -> None:
    """Log the action execution."""
    self.logger.info(f"User {request.user_id} performed {request.action}")
```

#### Replace Magic Values
```python
# BEFORE
class Config:
    def __init__(self):
        self.timeout = 30
        self.retries = 3
        self.batch_size = 100

# AFTER
class Config:
    """Configuration with sensible defaults."""

    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BATCH_SIZE = 100

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_MAX_RETRIES,
        batch_size: int = DEFAULT_BATCH_SIZE
    ) -> None:
        """Initialize configuration."""
        self.timeout = timeout
        self.retries = retries
        self.batch_size = batch_size
```

#### Simplify Complex Conditionals
```python
# BEFORE
def should_process(self, item):
    if item.status == "active" and (item.priority > 5 or item.urgent) and item.assigned_to is not None:
        return True
    return False

# AFTER
def should_process(self, item: Item) -> bool:
    """Determine if item should be processed."""
    return (
        self._is_active(item)
        and self._is_high_priority(item)
        and self._is_assigned(item)
    )

def _is_active(self, item: Item) -> bool:
    """Check if item is active."""
    return item.status == "active"

def _is_high_priority(self, item: Item) -> bool:
    """Check if item is high priority or urgent."""
    return item.priority > 5 or item.urgent

def _is_assigned(self, item: Item) -> bool:
    """Check if item is assigned."""
    return item.assigned_to is not None
```

### 6. Final Commit

After all refactoring complete:

```bash
cd /Users/sanchay/Documents/open-code-blocks

# Verify everything works
pytest tests/ -v --cov=ob1 --cov-report=term-missing
mypy ob1/
black ob1/ tests/
flake8 ob1/

# Final commit (if you haven't been committing incrementally)
git add ob1/{module_name}
git commit -m "refactor: improve code quality in {module_name}

- Add complete type hints throughout
- Extract complex logic to helper methods
- Improve variable and method naming
- Add comprehensive docstrings
- Maintain 100% test pass rate
- Coverage: {XX}%

TDD REFACTOR phase complete."
```

## What NOT to Do

- **DON'T** change behavior - only improve structure
- **DON'T** add new features - that requires new tests first
- **DON'T** skip running tests after changes
- **DON'T** make multiple changes before testing
- **DON'T** continue if tests fail - revert and try smaller change
- **DON'T** remove or modify tests

## Success Criteria

- [ ] All tests still passing (100% green)
- [ ] Type hints complete on all public APIs
- [ ] Docstrings on all classes and public methods
- [ ] No files over 300 lines
- [ ] No magic numbers - extracted to named constants
- [ ] Complex logic extracted to helper methods
- [ ] Descriptive variable/method names
- [ ] mypy passes with no errors
- [ ] black formatting applied
- [ ] Coverage maintained or improved
- [ ] Changes committed

## Next Steps

After REFACTOR phase:
1. Run `/tdd-red` to start adding new features
2. Or run `/tdd-cycle` to start a complete new TDD cycle

---

**Remember:** Refactoring is about making code better WITHOUT changing behavior. Tests are your safety net - use them!

**When in doubt, ask: "Did I run the tests after this change?" If no, run them NOW.**
