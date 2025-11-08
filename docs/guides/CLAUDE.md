# ob1 - Parallel AI SWE Orchestrator

**Mission:** Orchestrate multiple AI agents to work on the same task in parallel, creating competing pull requests.

## 🎯 Development Philosophy: STRICT TDD

This project follows **Test-Driven Development (TDD)** exclusively.

### The Golden Rule

**NEVER write production code without a failing test first.**

## TDD Workflow - MANDATORY

### Phase 1: RED - Write Failing Tests

Before ANY production code:

1. **Write comprehensive tests** that import functionality that doesn't exist yet
2. **Run pytest** to confirm tests fail (RED)
3. **Commit tests** with message: `test: add tests for [feature]`

**Prompt Template:**
```
"We're using TDD. Write failing tests for [FEATURE] that cover:
1. [Test case 1]
2. [Test case 2]
3. [Edge case]

Don't implement the code yet - just write the tests.
Run pytest to confirm they fail."
```

### Phase 2: GREEN - Minimal Implementation

Only after committing failing tests:

1. **Implement minimal code** to make tests pass
2. **Run tests iteratively** after each change
3. **DO NOT modify tests** during implementation
4. **When all pass**, commit with: `feat: implement [feature]`

**Prompt Template:**
```
"Now implement [MODULE/CLASS] to make all tests pass.
Don't modify the tests. Iterate until all tests pass."
```

### Phase 3: REFACTOR - Improve Quality

Only after tests pass:

1. **Refactor code** for quality, readability, performance
2. **Run tests after each change** to ensure they still pass
3. **Commit** with: `refactor: improve [component]`

**Prompt Template:**
```
"Refactor [MODULE] to:
- Add type hints
- Improve naming
- Extract helpers
Run tests after each change."
```

## Project Structure

```
ob1/
├── __init__.py
├── cli.py              # Typer CLI interface
├── orchestrator.py     # Main orchestration logic
├── agents/
│   ├── __init__.py
│   └── claude.py       # Claude Agent SDK wrapper
├── workspace/
│   ├── __init__.py
│   ├── worktree.py     # Git worktree management
│   └── github_pr.py    # PR creation
└── utils/
    ├── __init__.py
    ├── config.py       # Configuration management
    └── logger.py       # Logging utilities

tests/
├── unit/               # Fast, isolated tests
├── integration/        # Multi-component tests
├── conftest.py         # Shared fixtures
└── __init__.py
```

## Code Quality Standards

### Type Hints - MANDATORY

All functions must have complete type hints:

```python
async def create_pr(
    repo: str,
    title: str,
    head: str,
    base: str = "main"
) -> PullRequest:
    ...
```

### Async/Await - MANDATORY for I/O

All I/O operations must be async:
- HTTP: `httpx.AsyncClient`
- Subprocess: `asyncio.create_subprocess_exec`

### File Size Limit

**No file > 300 lines.** Extract to separate modules if needed.

### Single Responsibility

Each module does ONE thing well.

## Testing Standards

### Test Markers

```python
@pytest.mark.unit           # Fast unit test
@pytest.mark.integration    # Integration test
@pytest.mark.async          # Async test
@pytest.mark.slow           # Skip in dev
```

### Coverage Requirements

- **Minimum**: 80% overall
- **Critical paths**: 95%+ (orchestrator, github_pr, cli)

### Running Tests

```bash
# All tests with coverage
pytest

# Unit tests only (fast)
pytest tests/unit -v

# Watch mode
ptw

# Parallel
pytest -n auto
```

## Common Commands

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format
black ob1/ tests/

# Type check
mypy ob1/

# Lint
flake8 ob1/ tests/
```

## Prompting Guidelines

### Good Prompts ✅

- "We're using TDD. Write tests first for [feature]."
- "Don't implement yet - only write the tests."
- "Run pytest to confirm tests fail."
- "Now implement to make tests pass."

### Bad Prompts ❌

- "Add feature X" (unclear if TDD)
- "Write some tests" (when? before or after?)
- "Implement and test..." (wrong order)

## CI/CD Requirements

All PRs must:
1. ✅ Pass all tests
2. ✅ Maintain 80%+ coverage
3. ✅ Pass type checking (mypy)
4. ✅ Pass linting (black, flake8)

## Architecture Principles

1. **Async-first** - All I/O is async
2. **Type-safe** - Complete type hints
3. **Testable** - Dependency injection, mockable
4. **Modular** - Single responsibility, <300 lines
5. **Observable** - Structured logging

## Environment Variables

Required:
- `GITHUB_TOKEN` - GitHub personal access token
- `ANTHROPIC_API_KEY` - Claude API key

## Notes for Claude Code

- **ALWAYS** write tests before implementation
- **NEVER** skip the RED phase
- **ALWAYS** run tests after each change
- **NEVER** modify tests during implementation
- **ALWAYS** use async/await for I/O
- **ALWAYS** add type hints
- **KEEP** files under 300 lines

**When in doubt, ask: "Should we write tests first?"**

**The answer is always YES.**
