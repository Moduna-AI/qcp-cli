"""Local, credential-free storage for database schema snapshots."""

from __future__ import annotations

import json
import os
import stat
from abc import ABC, abstractmethod
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from qcp import config as cfg
from qcp.models import SchemaSnapshot

SCHEMA_CACHE_TTL = timedelta(hours=24)
SCHEMA_CACHE_VERSION = 2


class SchemaMemoryStore(ABC):
    """Contract for persisting schema metadata across CLI runs."""

    @abstractmethod
    def recall(self, database_id: str) -> SchemaSnapshot | None:
        """Return a fresh snapshot for a database, if one exists."""

    @abstractmethod
    def store(self, snapshot: SchemaSnapshot) -> None:
        """Persist a schema snapshot."""

    @abstractmethod
    def invalidate(self, database_id: str) -> None:
        """Remove cached schema for a database."""


class JsonSchemaMemoryStore(SchemaMemoryStore):
    """Store isolated schema snapshots in ``~/.qcp/schema.json``."""

    def __init__(self, path: Path | None = None, ttl: timedelta = SCHEMA_CACHE_TTL) -> None:
        """Initialize the JSON store and its freshness policy."""
        self._path = path
        self._ttl = ttl

    @property
    def path(self) -> Path:
        """Return the current cache path, respecting test-time QCP_HOME overrides."""
        return self._path or cfg.CONFIG_DIR / "schema.json"

    def _load_all(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError, OSError:
            return {}

    def recall(self, database_id: str) -> SchemaSnapshot | None:
        """Return a fresh, valid snapshot without exposing other databases."""
        raw_snapshot = self._load_all().get(database_id)
        if not isinstance(raw_snapshot, dict) or raw_snapshot.get("format_version") != SCHEMA_CACHE_VERSION:
            return None
        try:
            snapshot = SchemaSnapshot.model_validate(raw_snapshot)
        except ValidationError:
            return None
        captured_at = snapshot.captured_at
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=UTC)
        if datetime.now(UTC) - captured_at > self._ttl:
            return None
        return snapshot

    def store(self, snapshot: SchemaSnapshot) -> None:
        """Persist one validated snapshot with owner-only permissions."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with suppress(OSError):
            os.chmod(self.path.parent, stat.S_IRWXU)
        snapshots = self._load_all()
        snapshots[snapshot.database_id] = snapshot.model_dump(mode="json")
        self.path.write_text(json.dumps(snapshots, indent=2), encoding="utf-8")
        with suppress(OSError):
            os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)

    def invalidate(self, database_id: str) -> None:
        """Remove one database's snapshot while preserving all others."""
        snapshots = self._load_all()
        if database_id not in snapshots:
            return
        del snapshots[database_id]
        self.path.write_text(json.dumps(snapshots, indent=2), encoding="utf-8")
