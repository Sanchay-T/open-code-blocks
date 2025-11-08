"""
Logging utilities for ob1.
"""
import logging
from rich.logging import RichHandler


def setup_logger(name: str = "ob1", level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with Rich formatting.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Add rich handler
    handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_path=False
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger
