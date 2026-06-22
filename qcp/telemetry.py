"""Collect telemetry to track installs."""

import contextlib
import hashlib
import platform
import sys
import uuid
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import httpx

POSTHOG_API_KEY = "phc_pLMwKnLTd5oyY6aKwWRjnKwPz2vfXnZuSKnaxyGCbHKk"
POSTHOG_ENDPOINT = "https://us.i.posthog.com/capture/"
CONFIG_PATH = Path.home() / ".qcp" / "config.json"

try:
    __version__ = version("qcp-cli")
except PackageNotFoundError:
    __version__ = "0+unknown"


def get_machine_id() -> str:
    """Derives a stable ID from machine hardware. Survives config deletion."""
    sources = [
        str(uuid.getnode()),  # MAC address
        platform.node(),  # hostname
        platform.machine(),  # hardware type e.g. x86_64
        platform.processor(),  # CPU info
    ]
    fingerprint = "|".join(sources).encode()
    return hashlib.sha256(fingerprint).hexdigest()[:32]


def get_install_id() -> str:
    """Setup an install id for a new user."""
    import json

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    if "install_id" not in config:
        config["install_id"] = get_machine_id()
        CONFIG_PATH.write_text(json.dumps(config, indent=2))
    return config["install_id"]


def track(event: str, props: dict | None = None) -> None:
    """Track a new user."""
    import json

    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    if not config.get("telemetry", True):
        return
    if props is None:
        props = {}
    with contextlib.suppress(Exception):
        httpx.post(
            POSTHOG_ENDPOINT,
            json={
                "api_key": POSTHOG_API_KEY,
                "event": event,
                "distinct_id": get_install_id(),
                "properties": {
                    "os": platform.system().lower(),
                    "version": __version__,
                    **props,
                },
            },
            timeout=2,
        )


# telemetry.py


def ask_consent() -> None:
    """Ask user for telemetry consent on first run."""
    import json

    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}

    if "telemetry" in config:
        return  # already answered, don't ask again

    # Non-interactive environment — disable telemetry silently
    if not sys.stdin.isatty():
        config["telemetry"] = False
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(config, indent=2))
        return

    print("\n📊 Help improve qcp?")
    print("   qcp collects anonymous usage data (no queries, no schema, no personal data).")
    print("   To opt out anytime: qcp config --telemetry off\n")

    response = input("   Allow anonymous telemetry? [Y/n]: ").strip().lower()
    config["telemetry"] = response not in ("n", "no")

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))

    if config["telemetry"]:
        print("   ✅ Thanks! Telemetry enabled.\n")
        track("telemetry_accepted")
    else:
        print("   ✅ Got it. Telemetry disabled.\n")


def set_consent(enabled: bool) -> None:
    """Programmatically set telemetry consent."""
    import json

    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    config["telemetry"] = enabled
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    print(f"   Telemetry {'enabled' if enabled else 'disabled'}.")
