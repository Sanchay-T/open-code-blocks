"""Agent panel renderer for beautiful individual agent displays."""

from typing import Dict, Any, Optional
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from .theme import PROVIDER_COLORS, PROVIDER_EMOJIS, STATUS_EMOJIS, PHASE_EMOJIS, PROGRESS_FULL, PROGRESS_EMPTY


class AgentPanel:
    """Renders a beautiful panel for a single agent."""

    def __init__(self, agent_name: str, provider: str):
        self.agent_name = agent_name
        self.provider = provider
        self.color = PROVIDER_COLORS.get(provider, "white")
        self.status = "pending"
        self.metrics = {
            'elapsed': 0,
            'files': 0,
            'tools': 0,
            'diff_lines': 0,
        }
        self.current_activity = "Initializing..."
        self.phases: Dict[str, Dict[str, Any]] = {}
        self.pr_url: Optional[str] = None
        self.error: Optional[str] = None

    def update_status(self, status: str) -> None:
        """Update agent status."""
        self.status = status

    def update_metrics(self, **kwargs) -> None:
        """Update agent metrics."""
        self.metrics.update(kwargs)

    def update_activity(self, activity: str) -> None:
        """Update current activity."""
        self.current_activity = activity

    def update_phase(self, phase_name: str, complete: bool = False, duration: float = 0.0) -> None:
        """Update phase information."""
        self.phases[phase_name] = {
            'complete': complete,
            'duration': duration
        }

    def set_pr_url(self, url: str) -> None:
        """Set PR URL."""
        self.pr_url = url

    def set_error(self, error: str) -> None:
        """Set error message."""
        self.error = error

    def render(self) -> Panel:
        """Generate Rich Panel for this agent."""
        emoji = PROVIDER_EMOJIS.get(self.provider, "⚪")
        status_emoji = STATUS_EMOJIS.get(self.status, "")

        # Build content
        content_parts = []

        # Metrics line
        metrics_line = (
            f"⏱  {self._format_time(self.metrics['elapsed'])}  │  "
            f"📝 {self.metrics['files']} files  │  "
            f"🛠️  {self.metrics['tools']} tools"
        )
        if self.metrics.get('diff_lines', 0) > 0:
            metrics_line += f"  │  +{self.metrics['diff_lines']} lines"

        content_parts.append(metrics_line)
        content_parts.append("")

        # Phase progress (if any)
        if self.phases:
            for phase_name, phase_data in self.phases.items():
                emoji_icon = PHASE_EMOJIS.get(phase_name, "")
                if phase_data['complete']:
                    bar = PROGRESS_FULL * 12
                    status_icon = "✓"
                    duration_str = f"({phase_data['duration']:.0f}s)" if phase_data['duration'] > 0 else ""
                else:
                    bar = PROGRESS_EMPTY * 12
                    status_icon = ""
                    duration_str = ""

                content_parts.append(
                    f"{emoji_icon} {phase_name.title():<15} {bar} {status_icon} {duration_str}"
                )
            content_parts.append("")

        # Current activity or error
        if self.status == "failed" and self.error:
            content_parts.append(f"[red]Error: {self.error[:60]}...[/red]")
        elif self.status == "running":
            # Progress bar for current operation
            progress_pct = self._estimate_progress()
            bar_width = 40
            filled = int(bar_width * progress_pct / 100)
            bar = PROGRESS_FULL * filled + PROGRESS_EMPTY * (bar_width - filled)
            content_parts.append(f"{bar}  {progress_pct}%")
            content_parts.append(f"[dim]{self.current_activity}[/dim]")
        elif self.status == "success":
            content_parts.append(self.current_activity)

        # PR link (if completed successfully)
        if self.pr_url:
            content_parts.append("")
            pr_num = self.pr_url.split("/")[-1]
            content_parts.append(f"🔗 [link={self.pr_url}]PR #{pr_num}[/link]")

        # Create panel
        title = f"{emoji} {self.agent_name.title()}"
        status_text = f"{status_emoji} {self.status.upper()}"

        # Choose border style based on status
        if self.status == "success":
            border_style = f"bold {self.color}"
        elif self.status == "failed":
            border_style = "bold red"
        elif self.status == "running":
            border_style = self.color
        else:
            border_style = f"dim {self.color}"

        panel = Panel(
            "\n".join(content_parts),
            title=title,
            subtitle=status_text,
            border_style=border_style,
            padding=(0, 1)
        )

        return panel

    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def _estimate_progress(self) -> int:
        """Estimate completion percentage based on completed phases."""
        if not self.phases:
            return 0

        phase_weights = {
            'discovery': 20,
            'implementation': 50,
            'verification': 20,
            'finalization': 10
        }

        completed = sum(
            phase_weights.get(name, 0)
            for name, data in self.phases.items()
            if data['complete']
        )

        # Never show 100% while running
        return min(completed, 99)
