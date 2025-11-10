"""Live dashboard for real-time multi-agent visualization."""

import time
from typing import Dict, Any, List
from rich.console import Console, Group
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from .agent_panel import AgentPanel
from .theme import PROGRESS_FULL, PROGRESS_EMPTY


class LiveDashboard:
    """Real-time dashboard for k parallel agents."""

    def __init__(self, agent_names: List[str], providers: List[str], task: str, console: Console):
        self.console = console
        self.task = task
        self.start_time = time.time()
        self.agent_panels: Dict[str, AgentPanel] = {}

        # Create agent panels
        for agent_name, provider in zip(agent_names, providers):
            self.agent_panels[agent_name] = AgentPanel(agent_name, provider)

    def create_header(self, completed: int, total: int) -> Panel:
        """Create dashboard header."""
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        time_str = f"{mins:02d}:{secs:02d}"

        header_text = (
            f"[bold cyan]🤖 OB1 ORCHESTRATOR[/bold cyan]"
            f"{'':>30}⏱️  {time_str} elapsed\n"
            f"[dim]Task: \"{self.task}\"[/dim]"
            f"{'':>20}📊 {completed}/{total} complete"
        )

        return Panel(header_text, border_style="bold cyan", padding=(0, 1))

    def create_footer(self, completed: int, total: int) -> Panel:
        """Create dashboard footer with overall progress."""
        progress_pct = int((completed / total) * 100) if total > 0 else 0
        bar_width = 50
        filled = int(bar_width * progress_pct / 100)
        bar = PROGRESS_FULL * filled + PROGRESS_EMPTY * (bar_width - filled)

        footer_text = f"Overall Progress: {bar}  {progress_pct}%  ({completed}/{total} agents)"
        return Panel(footer_text, border_style="dim cyan", padding=(0, 1))

    def update_agent(self, agent_name: str, **updates) -> None:
        """Update an agent's state."""
        if agent_name not in self.agent_panels:
            return

        panel = self.agent_panels[agent_name]

        if 'status' in updates:
            panel.update_status(updates['status'])
        if 'metrics' in updates:
            panel.update_metrics(**updates['metrics'])
        if 'activity' in updates:
            panel.update_activity(updates['activity'])
        if 'phase' in updates:
            phase_info = updates['phase']
            panel.update_phase(
                phase_info.get('name', ''),
                phase_info.get('complete', False),
                phase_info.get('duration', 0.0)
            )
        if 'pr_url' in updates:
            panel.set_pr_url(updates['pr_url'])
        if 'error' in updates:
            panel.set_error(updates['error'])

    def render(self) -> Group:
        """Render the complete dashboard."""
        # Count completed agents
        completed = sum(
            1 for panel in self.agent_panels.values()
            if panel.status in ('success', 'failed', 'dry-run')
        )
        total = len(self.agent_panels)

        # Build components
        components = []

        # Header
        components.append(self.create_header(completed, total))

        # Agent panels
        for panel in self.agent_panels.values():
            components.append(panel.render())

        # Footer
        components.append(self.create_footer(completed, total))

        return Group(*components)

    def get_completed_count(self) -> int:
        """Get number of completed agents."""
        return sum(
            1 for panel in self.agent_panels.values()
            if panel.status in ('success', 'failed', 'dry-run')
        )

    def is_complete(self) -> bool:
        """Check if all agents are done."""
        return self.get_completed_count() == len(self.agent_panels)

    def get_success_count(self) -> int:
        """Get number of successful agents."""
        return sum(
            1 for panel in self.agent_panels.values()
            if panel.status == 'success'
        )

    def get_failed_agents(self) -> List[Dict[str, str]]:
        """Get list of failed agents with errors."""
        failed = []
        for panel in self.agent_panels.values():
            if panel.status == 'failed':
                failed.append({
                    'name': panel.agent_name,
                    'error': panel.error or 'Unknown error'
                })
        return failed
