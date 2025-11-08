---
name: context-engine
description: Intelligent codebase understanding using context engine. Use when analyzing architecture, finding related code, understanding dependencies, or mapping code relationships. Excels at .py and .tsx files.
---

# Context Engine Skill

You are an expert at intelligently analyzing codebases, building context graphs, extracting symbols, and providing relevant code context to AI agents and developers.

## Core Capabilities

### 1. Repo Context Gathering

**Reference:** `/Users/sanchay/Documents/open-code-blocks/src/ob1/context_engine.py`

**Purpose:** Build focused context for AI agents working on specific tasks

**How it Works:**
1. Start from worktree root
2. Walk through directories matching scope patterns
3. Skip ignored directories (`.git`, `.ob1`, `node_modules`)
4. Collect files matching patterns (up to max_files)
5. Extract snippets from each file (up to max_chars_per_file)
6. Summarize package.json for project metadata

**Function Signature:**
```python
def gather_repo_context(
    worktree: Path,
    patterns: Iterable[str],
    max_files: int = 8,
    max_chars_per_file: int = 600,
) -> RepoContext
```

**Returns:**
```python
@dataclass
class RepoContext:
    file_snippets: List[str]  # Formatted code snippets
    package_summary: str      # Project metadata
```

### 2. Scope Pattern Filtering

**Reference:** `/Users/sanchay/Documents/open-code-blocks/src/ob1/path_filters.py`

**Pattern Syntax:**
- `**` - Match any directory depth
- `*` - Match any characters in filename
- Comma/semicolon separated: `"**/*.tsx,**/*.css"`
- Empty/None defaults to `["**"]` (everything)

**Examples:**
```python
# Frontend TypeScript files
patterns = ["frontend/src/**/*.tsx", "frontend/src/**/*.ts"]

# All Python files
patterns = ["**/*.py"]

# Specific directories
patterns = ["src/components/**", "src/utils/**"]

# Multiple file types
patterns = ["**/*.tsx", "**/*.css", "**/*.json"]
```

**Matching Logic:**
```python
def matches_any(path: str, patterns: Iterable[str]) -> bool:
    """Return True if path matches any pattern."""
    for pattern in patterns:
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False
```

### 3. File Snippet Extraction

**Format:**
```markdown
### frontend/src/components/Button.tsx
```text
import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  children: React.ReactNode;
  onClick?: () => void;
}

export function Button({ variant = 'primary', children, onClick }: ButtonProps) {
  return (
    <button
      className={cn('btn', `btn-${variant}`)}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```
```

**Extraction Rules:**
- Read UTF-8 text files only (skip binaries)
- Truncate to `max_chars_per_file` (default: 600 chars)
- Show beginning of file (most important: imports, types, main logic)
- Skip if UnicodeDecodeError

### 4. Package.json Summarization

**Purpose:** Provide project context to agents

**Extracts:**
- Package name
- Key scripts: `dev`, `build`, `preview`
- Top 6 dependencies

**Example Output:**
```
Package `frontend` scripts: {'dev': 'vite', 'build': 'vite build', 'preview': 'vite preview'}.
Key deps: react, react-dom, vite, tailwindcss, typescript, zustand.
```

**Code:**
```python
def _summarize_package_json(worktree: Path) -> str:
    pkg_path = worktree / "frontend" / "package.json"
    if not pkg_path.exists():
        return ""
    data = json.loads(pkg_path.read_text())
    name = data.get("name", "frontend")
    scripts = data.get("scripts", {})
    important_scripts = {k: scripts[k] for k in ["dev", "build", "preview"] if k in scripts}
    deps = list(data.get("dependencies", {}).keys())[:6]
    return f"Package `{name}` scripts: {important_scripts}. Key deps: {', '.join(deps)}."
```

### 5. Building Agent Prompts

**Function:**
```python
def build_prompt_text(
    task: str,
    scope_patterns: Iterable[str],
    context: RepoContext
) -> str
```

**Prompt Structure:**
```markdown
You are ob1, an elite frontend engineer. Implement the user request inside the allowed scope only.

Task:
[User's task description]

Constraints:
- Only edit files matching: [scope patterns]
- Changes must be buildable via `npm install && npm run build` inside `frontend/`.
- Keep code clean, typed (where relevant), and ensure responsive design.
- If a new page/component is created, update routing or App.jsx so it renders.

Project Summary:
[Package.json summary]

Important Files:
[File snippets from context]

Deliverables:
1. Implement the feature completely, including UI and minimal styling.
2. Provide client-side validation and friendly error states.
3. Keep copy concise and professional.

When finished, ensure `npm run build` would succeed. Do not remove unrelated code.
```

## Context Gathering Strategies

### Strategy 1: Focused Context

**When to use:** Task has narrow scope (e.g., "Add button to navbar")
**Approach:**
- Tight scope patterns: `["frontend/src/components/Navbar.tsx"]`
- Small max_files (1-3)
- More chars per file (800-1000)

### Strategy 2: Broad Context

**When to use:** Task requires understanding relationships (e.g., "Add new page")
**Approach:**
- Wide scope patterns: `["frontend/src/**/*.tsx"]`
- More max_files (8-15)
- Fewer chars per file (400-600)

### Strategy 3: Architecture Context

**When to use:** Understanding project structure
**Approach:**
- Include config files: `["package.json", "tsconfig.json", "vite.config.ts"]`
- Include key directories: `["src/pages/**", "src/components/**", "src/lib/**"]`
- Max files: 20+

### Strategy 4: Dependency Context

**When to use:** Understanding imports and relationships
**Approach:**
- Focus on shared utilities: `["src/lib/**", "src/utils/**", "src/hooks/**"]`
- Include type definitions: `["**/*.d.ts", "**/types.ts"]`
- More chars per file to see full exports

## Advanced Filtering

### Ignore Patterns

**Always Skip:**
- `.git/` - Git internals
- `.ob1/` - OB1 worktrees
- `node_modules/` - Dependencies
- `dist/`, `build/`, `.next/` - Build outputs
- `.env*` - Environment files (may contain secrets)

**Implementation:**
```python
ignore_roots = {".git", ".ob1", "node_modules"}
for path in sorted(worktree.rglob("*")):
    rel = path.relative_to(worktree).as_posix()
    if any(part in ignore_roots for part in rel.split("/")):
        continue  # Skip
```

### Path Normalization

**Always use POSIX paths:**
```python
rel = path.relative_to(worktree).as_posix()  # Uses "/" even on Windows
```

**Why:** Consistent pattern matching across platforms

### Binary File Handling

**Strategy:** Try to read as UTF-8, skip on error
```python
try:
    text = path.read_text(encoding="utf-8")
except UnicodeDecodeError:
    continue  # Skip binary files
```

## Context Optimization

### Token Budget Management

**Context is expensive:**
- Each file snippet adds tokens to agent prompt
- Balance breadth vs depth
- Prioritize files most relevant to task

**Tuning Knobs:**
```python
max_files = 8           # How many files to include
max_chars_per_file = 600  # How much of each file

# Total chars ≈ max_files * max_chars_per_file
# 8 * 600 = 4800 chars ≈ 1200 tokens
```

### Relevance Ranking

**Factors to consider:**
1. **Pattern Match Quality:** Exact match > wildcard match
2. **File Recency:** Recently modified files likely more relevant
3. **File Size:** Smaller files often more focused
4. **Dependency Depth:** Direct dependencies > transitive

**Current Implementation:**
- Simple: First N files matching patterns
- Improvement opportunity: Rank by relevance

### Caching Strategies

**When to cache:**
- Same scope patterns used repeatedly
- Static project structure
- Expensive to recompute

**What to cache:**
- File list for given patterns
- Package.json summary
- File snippets (invalidate on modification)

## Integration Points

### With Orchestrator

**Usage:** Provide context to each agent before execution
```python
context = await asyncio.to_thread(
    gather_repo_context,
    worktree_path,
    scope_patterns
)
prompt = build_prompt_text(task, scope_patterns, context)
await provider.run(agent_name, branch, prompt, worktree, repo_root)
```

### With Change Guard

**Usage:** Validate changes match original scope
```python
files = list_changed_files(worktree)
ensure_changes_within_scope(files, scope_patterns)
```

### With Providers

**Usage:** Inject context into agent prompts
- Claude Provider: Include in initial message
- Other providers: Adapt format as needed

## Best Practices

### 1. Scope Definition

**Do:**
- Be specific: `"frontend/src/components/**"` not `"**"`
- Include related files: Components + styles + tests
- Document intent: "Login page and auth components"

**Don't:**
- Use overly broad patterns without reason
- Mix unrelated concerns
- Include generated/build files

### 2. Context Quality

**Do:**
- Show file beginnings (imports, types, exports)
- Include comments and docstrings
- Preserve formatting for readability

**Don't:**
- Truncate mid-function (confusing)
- Include binary data
- Mix different languages in confusing ways

### 3. Performance

**Do:**
- Cache when appropriate
- Use asyncio.to_thread for I/O
- Limit max_files to reasonable number

**Don't:**
- Read entire files into memory unnecessarily
- Recursively walk ignored directories
- Block on I/O in async code

## Examples

### Example 1: Basic Context Gathering
```python
context = gather_repo_context(
    worktree=Path("/path/to/repo"),
    patterns=["src/**/*.tsx"],
    max_files=8,
    max_chars_per_file=600
)

print(f"Found {len(context.file_snippets)} files")
print(f"Project: {context.package_summary}")
```

### Example 2: Multi-Pattern Context
```python
patterns = [
    "frontend/src/components/**/*.tsx",
    "frontend/src/pages/**/*.tsx",
    "frontend/src/lib/**/*.ts"
]

context = gather_repo_context(
    worktree=worktree_path,
    patterns=patterns,
    max_files=15,
    max_chars_per_file=500
)
```

### Example 3: Full Prompt Generation
```python
context = gather_repo_context(worktree, patterns)

prompt = build_prompt_text(
    task="Add dark mode toggle to settings page",
    scope_patterns=["frontend/src/pages/Settings.tsx", "frontend/src/components/ThemeToggle.tsx"],
    context=context
)

# Send prompt to agent
result = await agent.run(prompt)
```

## Key Files Reference

- `/Users/sanchay/Documents/open-code-blocks/src/ob1/context_engine.py` - Main implementation
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/path_filters.py` - Pattern matching
- `/Users/sanchay/Documents/open-code-blocks/src/ob1/orchestrator.py` - Usage in orchestration

## When to Use This Skill

Use this skill when the user asks to:
- "Analyze this codebase"
- "Find all files related to X"
- "Understand the project structure"
- "What files should I modify for Y?"
- "Build context for implementing Z"
- "Show me the dependencies of module A"
- "Map out the component hierarchy"

This skill is essential for providing relevant, focused context to AI agents, enabling them to understand the codebase and make informed changes without overwhelming them with irrelevant information.
