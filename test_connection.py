#!/usr/bin/env python3
"""Quick diagnostic script to test OpenAI client connection."""
import json
import os
from pathlib import Path

from openai import OpenAI

CONFIG_PATH = Path(__file__).resolve().parent / "llm_config.json"

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
else:
    print("ERROR: llm_config.json not found")
    exit(1)

api_key = cfg.get("openai_api_key")
base_url = cfg.get("base_url") or cfg.get("api_base")
model = cfg.get("model", "gpt-4o-2024-08-06")

if not api_key:
    print("ERROR: No openai_api_key in config")
    exit(1)

print(f"API Key (masked): {api_key[:10]}...{api_key[-4:]}")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print()

try:
    if base_url:
        print(f"Creating OpenAI client with base_url={base_url}")
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        print("Creating OpenAI client (default endpoint)")
        client = OpenAI(api_key=api_key)

    print("Testing connection with a simple list models request...")
    # This will fail if credentials are wrong
    models = client.models.list()
    print(f"✓ Connection successful! Found {len(models.data)} models.")
except Exception as exc:
    print(f"✗ Connection failed: {exc}")
    exit(1)
