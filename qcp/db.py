"""PostgreSQL access with schema introspection and read-only enforcement."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.errors import InvalidSchemaName, UndefinedColumn, UndefinedTable

from qcp import config as cfg
from qcp.errors import (
    DatabaseConnectionError,
    NoDatabaseConfiguredError,
    SchemaChangedError,
    UnsafeQueryError,
)
from qcp.models import QueryResult, SchemaColumn, SchemaSnapshot, SchemaTable

MAX_QUERY_ROWS = 200
_READ_QUERY_PATTERN = re.compile(r"^\s*(select|with)\b", re.IGNORECASE)


class DatabaseClient(ABC):
    """Contract used by the database agent's PostgreSQL tools."""

    @property
    @abstractmethod
    def database_id(self) -> str:
        """Return a non-secret stable identifier for schema isolation."""

    @abstractmethod
    def test_connection(self) -> None:
        """Raise an application error when the database cannot be reached."""

    @abstractmethod
    def lookup_schema(self) -> SchemaSnapshot:
        """Read the public PostgreSQL schema."""

    @abstractmethod
    def execute_read_query(self, sql: str, limit: int = MAX_QUERY_ROWS) -> QueryResult:
        """Execute one read-only query and return at most ``limit`` rows."""


class PostgresDatabaseClient(DatabaseClient):
    """Psycopg 3 implementation of the QCP database contract."""

    def __init__(self, database_url: str) -> None:
        """Initialize the client with a PostgreSQL connection string."""
        self._database_url = database_url

    @property
    def database_id(self) -> str:
        """Return a credential-safe identifier for the configured database."""
        return hashlib.sha256(self._database_url.encode("utf-8")).hexdigest()[:16]

    def _connect(self) -> Connection[Any]:
        try:
            return psycopg.connect(self._database_url, connect_timeout=10)
        except Exception as error:
            raise DatabaseConnectionError(str(error)) from error

    def test_connection(self) -> None:
        """Verify that PostgreSQL accepts the configured connection string."""
        connection = self._connect()
        connection.close()

    def lookup_schema(self) -> SchemaSnapshot:
        """Return tables and columns from the PostgreSQL public schema."""
        sql = """
            SELECT table_schema, table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND table_schema NOT LIKE 'pg_toast%'
            ORDER BY table_schema, table_name, ordinal_position
        """
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
        except Exception as error:
            raise DatabaseConnectionError(str(error)) from error
        finally:
            connection.close()

        columns_by_table: dict[tuple[str, str], list[SchemaColumn]] = {}
        for schema_name, table_name, column_name, data_type, is_nullable in rows:
            table_key = (str(schema_name), str(table_name))
            columns_by_table.setdefault(table_key, []).append(
                SchemaColumn(name=str(column_name), data_type=str(data_type), nullable=is_nullable == "YES")
            )
        tables = [
            SchemaTable(schema_name=schema_name, name=table_name, columns=columns)
            for (schema_name, table_name), columns in columns_by_table.items()
        ]
        return SchemaSnapshot(database_id=self.database_id, captured_at=datetime.now(UTC), tables=tables)

    def execute_read_query(self, sql: str, limit: int = MAX_QUERY_ROWS) -> QueryResult:
        """Execute a single SELECT/CTE inside a read-only transaction."""
        normalized_sql = normalize_read_query(sql)
        connection = self._connect()
        try:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute(normalized_sql.encode("utf-8"))
                if cursor.description is None:
                    raise UnsafeQueryError(normalized_sql)
                columns = [_column_name(item) for item in cursor.description]
                fetched_rows: Sequence[Sequence[Any]] = cursor.fetchmany(limit + 1)
        except (UndefinedTable, UndefinedColumn, InvalidSchemaName) as error:
            raise SchemaChangedError(str(error)) from error
        except (UnsafeQueryError, SchemaChangedError):
            raise
        except Exception as error:
            raise DatabaseConnectionError(str(error)) from error
        finally:
            connection.close()

        truncated = len(fetched_rows) > limit
        rows = [list(row) for row in fetched_rows[:limit]]
        return QueryResult(sql=normalized_sql, columns=columns, rows=rows, truncated=truncated)


def _column_name(description: Any) -> str:
    """Read a column name from Psycopg or a DB-API-compatible test double."""
    return str(description.name if hasattr(description, "name") else description[0])


def normalize_read_query(sql: str) -> str:
    """Validate and normalize a single PostgreSQL SELECT or WITH statement."""
    normalized = sql.strip()
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip()
    candidate = normalized.lstrip("(").lstrip()
    if not normalized or ";" in normalized or not _READ_QUERY_PATTERN.match(candidate):
        raise UnsafeQueryError(sql)
    return normalized


def is_read_only(sql: str) -> bool:
    """Return whether SQL passes QCP's single read-statement validation."""
    try:
        normalize_read_query(sql)
    except UnsafeQueryError:
        return False
    return True


def require_db_url() -> str:
    """Return the configured database URL or raise a user-facing error."""
    database_url = cfg.get_db_url()
    if not database_url:
        raise NoDatabaseConfiguredError()
    return database_url


def test_connection(database_url: str) -> None:
    """Compatibility wrapper around :class:`PostgresDatabaseClient`."""
    PostgresDatabaseClient(database_url).test_connection()


def get_schema_summary(database_url: str, max_tables: int = 50) -> str:
    """Compatibility wrapper returning a compact schema string."""
    return PostgresDatabaseClient(database_url).lookup_schema().summary(max_tables=max_tables)


def run_query(database_url: str, sql: str, limit: int = MAX_QUERY_ROWS) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Compatibility wrapper returning DB-API-style columns and rows."""
    result = PostgresDatabaseClient(database_url).execute_read_query(sql, limit=limit)
    return result.columns, [tuple(row) for row in result.rows]
