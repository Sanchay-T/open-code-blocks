"""Visual theme configuration for OB1."""

# Provider color schemes
PROVIDER_COLORS = {
    "claude": "magenta",    # 🟣 Purple
    "cursor": "blue",       # 🔵 Blue
    "codex": "green",       # 🟢 Green
}

PROVIDER_EMOJIS = {
    "claude": "🟣",
    "cursor": "🔵",
    "codex": "🟢",
}

# Status indicators
STATUS_EMOJIS = {
    "pending": "⏸️",
    "running": "⏳",
    "success": "✓",
    "failed": "✗",
    "dry-run": "🔍"
}

# Phase indicators
PHASE_EMOJIS = {
    "discovery": "🔍",
    "implementation": "✏️",
    "verification": "🧪",
    "finalization": "🚀"
}

# Unicode box drawing characters
BOX_DOUBLE = "═"
BOX_SINGLE = "─"
BOX_HEAVY = "━"
CORNER_TL = "┌"
CORNER_TR = "┐"
CORNER_BL = "└"
CORNER_BR = "┘"
VERTICAL = "│"

# Progress bar characters
PROGRESS_FULL = "█"
PROGRESS_EMPTY = "░"
PROGRESS_PARTIAL = ["▏", "▎", "▍", "▌", "▋", "▊", "▉"]
