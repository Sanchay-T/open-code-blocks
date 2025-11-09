#!/usr/bin/env python3
"""Simple OpenAI GPT-4o smoke test."""
from __future__ import annotations

import os

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY before running this script.")

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a quick diagnostic bot."},
            {"role": "user", "content": "Reply with a single sentence confirming this key works."},
        ],
        max_tokens=50,
    )
    print(resp.choices[0].message.content.strip())

if __name__ == "__main__":
    main()
