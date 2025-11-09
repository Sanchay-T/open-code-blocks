#!/usr/bin/env python3
"""Minimal Claude Agent SDK smoke test."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query
from dotenv import load_dotenv


async def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise RuntimeError("Set CLAUDE_API_KEY before running this script.")

    os.environ.setdefault("CLAUDE_API_KEY", api_key)
    prompt = "Reply with 'Claude OK' if you can read this message."
    options = ClaudeAgentOptions(permission_mode="default")

    async for message in query(prompt=prompt, options=options):
        content = getattr(message, "content", None)
        if content:
            text = " ".join(getattr(block, "text", "") for block in content)
            if text.strip():
                print(text.strip())
                break


if __name__ == "__main__":
    asyncio.run(main())
