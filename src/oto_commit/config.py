import os
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".oto-commit-config.json"
ENV_VAR = "GEMINI_API_KEY"

def save_api_key(api_key: str):
    config = {"api_key": api_key}
    # Dosya daha ilk anda yalnızca sahibinin okuyabileceği izinle (0600) açılır;
    # chmod ise daha önce 0644 ile oluşturulmuş eski dosyaları da düzeltir.
    fd = os.open(CONFIG_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(config, f)
    os.chmod(CONFIG_FILE, 0o600)

def load_api_key() -> str:
    env_key = os.environ.get(ENV_VAR)
    if env_key:
        return env_key
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("api_key")
    except (ValueError, OSError, AttributeError):
        return None
