"""Config storage for qcp.

Config lives at ~/.qcp/config.json. Keeps things minimal: a flat
dict with a few known keys. No external deps beyond stdlib.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, Optional

CONFIG_DIR = Path(os.environ.get("QCP_HOME", Path.home() / ".qcp"))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_PROVIDER = "gemini"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(CONFIG_DIR, stat.S_IRWXU)  # 0700, owner only
    except OSError:
        pass


def load() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save(data: dict[str, Any]) -> None:
    _ensure_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        pass


def get(key: str, default: Optional[Any] = None) -> Any:
    return load().get(key, default)


def set_key(key: str, value: Any) -> None:
    data = load()
    data[key] = value
    save(data)


def unset_key(key: str) -> None:
    data = load()
    if key in data:
        del data[key]
        save(data)


# Convenience accessors -----------------------------------------------------

def get_db_url() -> Optional[str]:
    """DB url resolution order: env var QCP_DATABASE_URL > config file."""
    return os.environ.get("QCP_DATABASE_URL") or get("database_url")


def get_gemini_api_key() -> Optional[str]:
    """API key resolution order: env var GEMINI_API_KEY > config file."""
    return os.environ.get("GEMINI_API_KEY") or get("gemini_api_key")


def get_provider() -> str:
    return get("provider", DEFAULT_PROVIDER)


def config_path() -> str:
    return str(CONFIG_FILE)
