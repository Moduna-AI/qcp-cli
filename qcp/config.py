"""Validated configuration storage for QCP."""

from __future__ import annotations

import json
import os
import stat
from contextlib import suppress
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from qcp.models import QcpConfig

CONFIG_DIR = Path(os.environ.get("QCP_HOME", Path.home() / ".qcp"))
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_PROVIDER = "gemini"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        os.chmod(CONFIG_DIR, stat.S_IRWXU)


def load() -> dict[str, Any]:
    """Load validated configuration, treating corrupt files as empty."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        raw_data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return QcpConfig.model_validate(raw_data).model_dump(mode="json", exclude_none=True)
    except (json.JSONDecodeError, OSError, ValidationError):
        return {}


def save(data: dict[str, Any]) -> None:
    """Validate and persist configuration with owner-only permissions."""
    validated = QcpConfig.model_validate(data)
    serialized = validated.model_dump(mode="json", exclude_none=True)
    _ensure_dir()
    CONFIG_FILE.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    with suppress(OSError):
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)


def get(key: str, default: Any = None) -> Any:
    """Return a configuration value by its persisted key."""
    return load().get(key, default)


def set_key(key: str, value: Any) -> None:
    """Set and validate one configuration value."""
    data = load()
    data[key] = value
    save(data)


def unset_key(key: str) -> None:
    """Remove one configuration value when present."""
    data = load()
    if key in data:
        del data[key]
        save(data)


def get_db_url() -> str | None:
    """Resolve the database URL, preferring ``QCP_DATABASE_URL``."""
    return os.environ.get("QCP_DATABASE_URL") or get("database_url")


def get_gemini_api_key() -> str | None:
    """Resolve the Gemini key, preferring ``GEMINI_API_KEY``."""
    return os.environ.get("GEMINI_API_KEY") or get("gemini_api_key")


def get_provider() -> str:
    """Return the configured language-model provider."""
    return str(get("provider", DEFAULT_PROVIDER))


def config_path() -> str:
    """Return the configuration path for status output."""
    return str(CONFIG_FILE)
