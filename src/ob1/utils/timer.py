"""Time tracking utilities."""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentTimer:
    """Track agent execution time."""

    start_time: float
    end_time: Optional[float] = None

    @classmethod
    def start(cls) -> 'AgentTimer':
        """Start a new timer."""
        return cls(start_time=time.time())

    def stop(self) -> None:
        """Stop the timer."""
        self.end_time = time.time()

    @property
    def elapsed(self) -> int:
        """Get elapsed time in seconds."""
        end = self.end_time or time.time()
        return int(end - self.start_time)

    def format(self) -> str:
        """Format elapsed time as MM:SS."""
        elapsed = self.elapsed
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins:02d}:{secs:02d}"

    @property
    def elapsed_float(self) -> float:
        """Get precise elapsed time in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
