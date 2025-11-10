"""Beautiful UI components for OB1 orchestrator."""

from .dashboard import LiveDashboard
from .agent_panel import AgentPanel
from .theme import PROVIDER_COLORS, PROVIDER_EMOJIS, STATUS_EMOJIS, PHASE_EMOJIS
from .animations import show_splash, celebrate_success, show_error_summary

__all__ = [
    "LiveDashboard",
    "AgentPanel",
    "PROVIDER_COLORS",
    "PROVIDER_EMOJIS",
    "STATUS_EMOJIS",
    "PHASE_EMOJIS",
    "show_splash",
    "celebrate_success",
    "show_error_summary",
]
