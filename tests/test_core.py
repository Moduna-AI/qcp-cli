import json
import os

import pytest

from qcp import config as cfg
from qcp import db
from qcp.errors import NoApiKeyConfiguredError, NoDatabaseConfiguredError, UnsafeQueryError


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp_path / ".qcp")
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp_path / ".qcp" / "config.json")
    monkeypatch.delenv("QCP_DATABASE_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    yield


def test_set_and_get_key():
    cfg.set_key("database_url", "postgresql://u:p@host:5432/db")
    assert cfg.get_db_url() == "postgresql://u:p@host:5432/db"


def test_unset_key():
    cfg.set_key("gemini_api_key", "abc123")
    cfg.unset_key("gemini_api_key")
    assert cfg.get_gemini_api_key() is None


def test_env_var_overrides_config(monkeypatch):
    cfg.set_key("database_url", "postgresql://from-config")
    monkeypatch.setenv("QCP_DATABASE_URL", "postgresql://from-env")
    assert cfg.get_db_url() == "postgresql://from-env"


def test_require_db_url_raises_when_missing():
    with pytest.raises(NoDatabaseConfiguredError):
        db.require_db_url()


def test_is_read_only_accepts_select_and_with():
    assert db.is_read_only("SELECT * FROM users")
    assert db.is_read_only("  with t as (select 1) select * from t")
    assert db.is_read_only("(select 1)")


def test_is_read_only_rejects_writes():
    assert not db.is_read_only("DELETE FROM users")
    assert not db.is_read_only("UPDATE users SET name = 'x'")
    assert not db.is_read_only("DROP TABLE users")


def test_run_query_blocks_unsafe_sql_without_connecting(monkeypatch):
    def fail_connect(_url):
        raise AssertionError("should not connect for unsafe SQL")

    monkeypatch.setattr(db, "_connect", fail_connect)
    with pytest.raises(UnsafeQueryError):
        db.run_query("postgresql://x", "DELETE FROM users")


def test_default_provider_is_gemini():
    assert cfg.get_provider() == "gemini"
