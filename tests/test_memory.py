from __future__ import annotations

import json
import stat
from datetime import UTC, datetime, timedelta

from qcp.memory import JsonSchemaMemoryStore
from qcp.models import SchemaColumn, SchemaSnapshot, SchemaTable


def make_snapshot(database_id: str, captured_at: datetime | None = None) -> SchemaSnapshot:
    return SchemaSnapshot(
        database_id=database_id,
        captured_at=captured_at or datetime.now(UTC),
        tables=[SchemaTable(name="users", columns=[SchemaColumn(name="id", data_type="integer", nullable=False)])],
    )


def test_memory_round_trip_and_owner_only_permissions(tmp_path):
    path = tmp_path / ".qcp" / "schema.json"
    store = JsonSchemaMemoryStore(path)
    snapshot = make_snapshot("database-a")

    store.store(snapshot)

    assert store.recall("database-a") == snapshot
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_memory_expires_after_ttl(tmp_path):
    store = JsonSchemaMemoryStore(tmp_path / "schema.json")
    store.store(make_snapshot("database-a", datetime.now(UTC) - timedelta(hours=25)))
    assert store.recall("database-a") is None


def test_memory_isolates_databases_and_invalidates_one(tmp_path):
    store = JsonSchemaMemoryStore(tmp_path / "schema.json")
    store.store(make_snapshot("database-a"))
    store.store(make_snapshot("database-b"))

    store.invalidate("database-a")

    assert store.recall("database-a") is None
    assert store.recall("database-b") is not None


def test_memory_recovers_from_corrupt_json(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text("not-json", encoding="utf-8")
    store = JsonSchemaMemoryStore(path)

    assert store.recall("database-a") is None
    store.store(make_snapshot("database-a"))
    assert json.loads(path.read_text(encoding="utf-8"))["database-a"]


def test_memory_ignores_snapshots_from_the_public_only_format(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(
        json.dumps(
            {
                "database-a": {
                    "database_id": "database-a",
                    "captured_at": datetime.now(UTC).isoformat(),
                    "tables": [],
                }
            }
        ),
        encoding="utf-8",
    )

    assert JsonSchemaMemoryStore(path).recall("database-a") is None
