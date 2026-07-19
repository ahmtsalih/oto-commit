import os
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".oto-commit-config.json"

def save_api_key(api_key: str):
    config = {"api_key": api_key}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)

def load_api_key() -> str:
    if not CONFIG_FILE.exists():
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
        return config.get("api_key")