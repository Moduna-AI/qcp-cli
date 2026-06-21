from __future__ import annotations

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from qcp import config as cfg
from qcp import db
from qcp.db import PostgresDatabaseClient
from qcp.errors import NoDatabaseConfiguredError, UnsafeQueryError
from qcp.models import QcpConfig


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path / ".qcp")
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / ".qcp" / "config.json")
    monkeypatch.delenv("QCP_DATABASE_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_config_round_trip_preserves_secret_value():
    cfg.set_key("gemini_api_key", "abc123")
    assert cfg.get_gemini_api_key() == "abc123"
    assert "abc123" in cfg.CONFIG_FILE.read_text(encoding="utf-8")


def test_config_rejects_unknown_provider():
    with pytest.raises(ValidationError):
        QcpConfig(provider="unknown")


def test_env_var_overrides_config(monkeypatch):
    cfg.set_key("database_url", "postgresql://from-config")
    monkeypatch.setenv("QCP_DATABASE_URL", "postgresql://from-env")
    assert cfg.get_db_url() == "postgresql://from-env"


def test_require_db_url_raises_when_missing():
    with pytest.raises(NoDatabaseConfiguredError):
        db.require_db_url()


@pytest.mark.parametrize(
    "sql",
    ["SELECT * FROM users", "with t as (select 1) select * from t", "(select 1);"],
)
def test_is_read_only_accepts_single_read_queries(sql):
    assert db.is_read_only(sql)


@pytest.mark.parametrize(
    "sql",
    ["DELETE FROM users", "UPDATE users SET name = 'x'", "DROP TABLE users", "SELECT 1; DELETE FROM users"],
)
def test_is_read_only_rejects_writes_and_multiple_statements(sql):
    assert not db.is_read_only(sql)


class FakeCursor:
    def __init__(self, rows, description=None):
        self.rows = rows
        self.description = description
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql):
        self.executed.append(sql)

    def fetchall(self):
        return self.rows

    def fetchmany(self, limit):
        return self.rows[:limit]


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.read_only = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


def test_postgres_schema_lookup_returns_typed_snapshot(monkeypatch):
    cursor = FakeCursor(
        [
            ("ml", "models", "id", "integer", "NO"),
            ("ml", "models", "name", "text", "YES"),
        ]
    )
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db.psycopg, "connect", Mock(return_value=connection))

    snapshot = PostgresDatabaseClient("postgresql://example").lookup_schema()

    assert snapshot.tables[0].schema_name == "ml"
    assert snapshot.tables[0].name == "models"
    assert snapshot.tables[0].columns[1].nullable is True
    assert "ml.models" in snapshot.summary()
    assert connection.closed is True


def test_postgres_query_enforces_read_only_and_row_limit(monkeypatch):
    rows = [(number,) for number in range(202)]
    cursor = FakeCursor(rows, description=[("number",)])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db.psycopg, "connect", Mock(return_value=connection))

    result = PostgresDatabaseClient("postgresql://example").execute_read_query("SELECT number FROM values", limit=200)

    assert connection.read_only is True
    assert len(result.rows) == 200
    assert result.truncated is True
    assert result.columns == ["number"]
    assert cursor.executed == [b"SELECT number FROM values"]


def test_unsafe_query_is_blocked_before_connecting(monkeypatch):
    connect = Mock(side_effect=AssertionError("must not connect"))
    monkeypatch.setattr(db.psycopg, "connect", connect)

    with pytest.raises(UnsafeQueryError):
        PostgresDatabaseClient("postgresql://example").execute_read_query("DELETE FROM users")

    connect.assert_not_called()


def test_default_provider_is_gemini():
    assert cfg.get_provider() == "gemini"
