"""Quick sanity checks for OpenAI/Codex and Cursor credentials.

Usage:
    source .venv/bin/activate
    python scripts/validate_keys.py
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
CURSOR_ME_URL = "https://api.cursor.com/v0/me"


def check_openai() -> bool:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CODEX_CLI_KEY")
    if not api_key:
        print("[OpenAI] Missing OPENAI_API_KEY (or CODEX_CLI_KEY).", file=sys.stderr)
        return False
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = httpx.get(OPENAI_MODELS_URL, headers=headers, timeout=15)
    except httpx.HTTPError as exc:
        print(f"[OpenAI] Request failed: {exc}", file=sys.stderr)
        return False
    if resp.status_code == 200:
        print("[OpenAI] ✅ API key accepted.")
        return True
    print(f"[OpenAI] ❌ Status {resp.status_code}: {resp.text}", file=sys.stderr)
    return False


def check_cursor() -> bool:
    api_key = os.getenv("CURSOR_API_KEY")
    if not api_key:
        print("[Cursor] Missing CURSOR_API_KEY.", file=sys.stderr)
        return False
    auth_header = base64.b64encode(f"{api_key}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}
    try:
        resp = httpx.get(CURSOR_ME_URL, headers=headers, timeout=15)
    except httpx.HTTPError as exc:
        print(f"[Cursor] Request failed: {exc}", file=sys.stderr)
        return False
    if resp.status_code == 200:
        data = resp.json()
        name = data.get("apiKeyName", "(unknown)")
        print(f"[Cursor] ✅ API key accepted ({name}).")
        return True
    print(f"[Cursor] ❌ Status {resp.status_code}: {resp.text}", file=sys.stderr)
    return False


def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded secrets from {env_path}")
    else:
        print("Warning: .env not found; relying on current environment.", file=sys.stderr)
    print("Running credential sanity checks...\n")
    ok_openai = check_openai()
    ok_cursor = check_cursor()
    if ok_openai and ok_cursor:
        print("\nAll keys look good. You can rerun `ob1 run ...` now.")
    else:
        print("\nAt least one key failed validation. Fix the errors above before rerunning ob1.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
