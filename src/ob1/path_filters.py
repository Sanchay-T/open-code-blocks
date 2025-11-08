from __future__ import annotations

import fnmatch
from typing import Iterable, List


def parse_scope(scope: str | None) -> List[str]:
    """Turn a comma/space separated scope string into glob patterns.

    Defaults to ["**"] (everything) when scope is None/empty.
    """

    if not scope:
        return ["**"]

    raw_parts = [part.strip() for part in scope.replace(";", ",").split(",")]
    patterns = [part or "**" for part in raw_parts if part]
    return patterns or ["**"]


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    """Return True if the POSIX path matches any of the provided glob patterns."""

    pattern_list = list(patterns)
    if not pattern_list:
        return True
    for pattern in pattern_list:
        normalized = pattern or "**"
        if fnmatch.fnmatchcase(path, normalized):
            return True
    return False
