#!/usr/bin/env python3
"""
Embed all OB1 source code into a single markdown document for LLM analysis.

This script creates a comprehensive markdown file containing:
- Complete execution flow documentation
- Full source code of all relevant files
- Architecture diagrams
- State management details
"""

from pathlib import Path
import json


def main():
    repo_root = Path(__file__).parent
    output_file = repo_root / "COMPLETE_OB1_CODEBASE.md"

    # Files to embed
    source_files = [
        # Core orchestration
        "src/ob1/cli.py",
        "src/ob1/orchestrator.py",
        "src/ob1/state_manager.py",

        # Repository management
        "src/ob1/repo_manager.py",
        "src/ob1/git_ops.py",

        # Context and prompting
        "src/ob1/context_engine.py",
        "src/ob1/path_filters.py",

        # Providers
        "src/ob1/providers/base.py",
        "src/ob1/providers/claude.py",
        "src/ob1/providers/cursor.py",
        "src/ob1/providers/codex.py",

        # GitHub integration
        "src/ob1/github_api.py",

        # Diff and validation
        "src/ob1/diff_utils.py",
        "src/ob1/change_guard.py",

        # UI
        "src/ob1/ui/dashboard.py",
        "src/ob1/ui/agent_panel.py",
        "src/ob1/ui/animations.py",
        "src/ob1/ui/theme.py",

        # CLI commands
        "src/ob1/cli_status.py",

        # QA
        "src/ob1/qa_agent.py",
        "src/ob1/qa_tools.py",

        # Settings
        "src/ob1/settings.py",

        # Utils
        "src/ob1/utils/timer.py",
    ]

    documentation_files = [
        "COMPLETE_EXECUTION_TRACE.md",
        "AGENT_DESIGN_SYSTEM.md",
        "STAGE_1_COMPLETE.md",
        "STAGE_2_STATUS.md",
        "ISSUES_AND_FIXES.md",
    ]

    with output_file.open('w') as out:
        # Header
        out.write("# Complete OB1 Codebase Documentation\n\n")
        out.write("**Generated:** 2025-11-09\n\n")
        out.write("**Purpose:** Single-document reference containing all OB1 code, execution flows, and architecture\n\n")
        out.write("---\n\n")

        # Table of Contents
        out.write("## Table of Contents\n\n")
        out.write("1. [Execution Flow Documentation](#execution-flow-documentation)\n")
        out.write("2. [Architecture & Design](#architecture--design)\n")
        out.write("3. [Complete Source Code](#complete-source-code)\n")
        out.write("4. [Additional Documentation](#additional-documentation)\n\n")
        out.write("---\n\n")

        # Section 1: Execution Flow
        out.write("# 1. Execution Flow Documentation\n\n")

        exec_trace_file = repo_root / "COMPLETE_EXECUTION_TRACE.md"
        if exec_trace_file.exists():
            content = exec_trace_file.read_text()
            # Remove the title from the embedded doc
            if content.startswith("# "):
                content = content.split("\n", 1)[1]
            out.write(content)
            out.write("\n\n---\n\n")

        # Section 2: Architecture
        out.write("# 2. Architecture & Design\n\n")

        arch_file = repo_root / "AGENT_DESIGN_SYSTEM.md"
        if arch_file.exists():
            content = arch_file.read_text()
            if content.startswith("# "):
                content = content.split("\n", 1)[1]
            out.write(content)
            out.write("\n\n---\n\n")

        # Section 3: Complete Source Code
        out.write("# 3. Complete Source Code\n\n")
        out.write("All source files with line numbers for reference.\n\n")

        for file_path_str in source_files:
            file_path = repo_root / file_path_str
            if not file_path.exists():
                out.write(f"## {file_path_str}\n\n")
                out.write(f"**Status:** File not found\n\n")
                continue

            out.write(f"## {file_path_str}\n\n")
            out.write(f"**Path:** `{file_path}`\n\n")

            # Get file stats
            lines = file_path.read_text().splitlines()
            out.write(f"**Lines:** {len(lines)}\n\n")

            # Embed source with line numbers
            out.write("```python\n")
            for i, line in enumerate(lines, 1):
                out.write(f"{i:5d} | {line}\n")
            out.write("```\n\n")
            out.write("---\n\n")

        # Section 4: Additional Documentation
        out.write("# 4. Additional Documentation\n\n")

        for doc_file_str in documentation_files:
            doc_file = repo_root / doc_file_str
            if not doc_file.exists() or doc_file_str in ["COMPLETE_EXECUTION_TRACE.md", "AGENT_DESIGN_SYSTEM.md"]:
                continue

            out.write(f"## {doc_file_str}\n\n")
            content = doc_file.read_text()
            out.write(content)
            out.write("\n\n---\n\n")

        # Appendix: State File Examples
        out.write("# Appendix: State File Examples\n\n")

        out.write("## Example: `.ob1/state/runs.json`\n\n")
        out.write("```json\n")
        example_runs = {
            "runs": [
                {
                    "run_id": "20251109-143025",
                    "message": "Build a login page",
                    "target_repo": "Sanchay-T/ob1-sandbox",
                    "base_branch": "main",
                    "scope_patterns": ["frontend/**"],
                    "issue_number": 42,
                    "k": 3,
                    "created_at": "2025-11-09T14:30:25.123Z",
                    "status": "completed",
                    "agents": [
                        {
                            "name": "claude-1",
                            "provider": "claude",
                            "branch": "ob1/20251109-143025/claude-1",
                            "status": "success",
                            "pr_number": 25,
                            "pr_url": "https://github.com/Sanchay-T/ob1-sandbox/pull/25",
                            "started_at": "2025-11-09T14:30:26Z",
                            "completed_at": "2025-11-09T14:35:42Z",
                            "error_message": None,
                            "metrics": {}
                        },
                        {
                            "name": "cursor-2",
                            "provider": "cursor",
                            "branch": "ob1/20251109-143025/cursor-2",
                            "status": "success",
                            "pr_number": 26,
                            "pr_url": "https://github.com/Sanchay-T/ob1-sandbox/pull/26",
                            "started_at": "2025-11-09T14:30:26Z",
                            "completed_at": "2025-11-09T14:34:15Z",
                            "error_message": None,
                            "metrics": {}
                        },
                        {
                            "name": "codex-3",
                            "provider": "codex",
                            "branch": "ob1/20251109-143025/codex-3",
                            "status": "success",
                            "pr_number": 27,
                            "pr_url": "https://github.com/Sanchay-T/ob1-sandbox/pull/27",
                            "started_at": "2025-11-09T14:30:26Z",
                            "completed_at": "2025-11-09T14:33:50Z",
                            "error_message": None,
                            "metrics": {}
                        }
                    ]
                }
            ]
        }
        json.dump(example_runs, out, indent=2)
        out.write("\n```\n\n")

        out.write("## Example: `.ob1/state/pr_tracking.json`\n\n")
        out.write("```json\n")
        example_prs = {
            "prs": [
                {
                    "pr_number": 25,
                    "repo": "Sanchay-T/ob1-sandbox",
                    "branch": "ob1/20251109-143025/claude-1",
                    "issue_number": 42,
                    "created_by_run": "20251109-143025",
                    "continuation_runs": [],
                    "last_updated": "2025-11-09T14:35:42Z",
                    "status": "open"
                },
                {
                    "pr_number": 26,
                    "repo": "Sanchay-T/ob1-sandbox",
                    "branch": "ob1/20251109-143025/cursor-2",
                    "issue_number": 42,
                    "created_by_run": "20251109-143025",
                    "continuation_runs": [],
                    "last_updated": "2025-11-09T14:34:15Z",
                    "status": "open"
                },
                {
                    "pr_number": 27,
                    "repo": "Sanchay-T/ob1-sandbox",
                    "branch": "ob1/20251109-143025/codex-3",
                    "issue_number": 42,
                    "created_by_run": "20251109-143025",
                    "continuation_runs": [],
                    "last_updated": "2025-11-09T14:33:50Z",
                    "status": "open"
                }
            ]
        }
        json.dump(example_prs, out, indent=2)
        out.write("\n```\n\n")

    print(f"✅ Complete codebase documentation generated: {output_file}")
    print(f"📊 File size: {output_file.stat().st_size / 1024:.1f} KB")
    print(f"📝 Ready to dump to LLM for analysis")


if __name__ == "__main__":
    main()
