"""Minimal Postgres helper used by qcp.

Wraps psycopg to: test connections, introspect schema (for grounding the
LLM's prompt), and run read-only queries safely.
"""
from __future__ import annotations

from .errors import DatabaseConnectionError, NoDatabaseConfiguredError, UnsafeQueryError
from . import config as cfg

# Statement prefixes that are allowed when running LLM-generated SQL.
_READ_ONLY_PREFIXES = ("select", "with")


def require_db_url() -> str:
    url = cfg.get_db_url()
    if not url:
        raise NoDatabaseConfiguredError()
    return url


def _connect(db_url: str):
    try:
        import psycopg2
        return psycopg2.connect(db_url, connect_timeout=10)
    except ImportError as e:
        raise DatabaseConnectionError(
            "no Postgres driver installed. Install with `pip install qcp[postgres]`."
        ) from e


def test_connection(db_url: str) -> None:
    try:
        conn = _connect(db_url)
        conn.close()
    except DatabaseConnectionError:
        raise
    except Exception as e:  # noqa: BLE001 - surface driver errors plainly
        raise DatabaseConnectionError(str(e)) from e


def get_schema_summary(db_url: str, max_tables: int = 50) -> str:
    """Return a compact text summary of tables/columns to ground the LLM."""
    query = """
        select table_name, column_name, data_type
        from information_schema.columns
        where table_schema = 'public'
        order by table_name, ordinal_position
    """
    conn = _connect(db_url)
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        raise DatabaseConnectionError(str(e)) from e
    finally:
        conn.close()

    tables: dict[str, list[str]] = {}
    for table_name, column_name, data_type in rows:
        tables.setdefault(table_name, []).append(f"{column_name} {data_type}")

    lines = []
    for i, (table, cols) in enumerate(tables.items()):
        if i >= max_tables:
            lines.append(f"... and {len(tables) - max_tables} more tables")
            break
        lines.append(f"- {table}({', '.join(cols)})")
    return "\n".join(lines) if lines else "(no tables found in 'public' schema)"


def is_read_only(sql: str) -> bool:
    cleaned = sql.strip().lstrip("(").strip().lower()
    return cleaned.startswith(_READ_ONLY_PREFIXES)


def run_query(db_url: str, sql: str, allow_write: bool = False, limit: int = 200) -> tuple[list[str], list[tuple]]:
    if not allow_write and not is_read_only(sql):
        raise UnsafeQueryError(sql)

    conn = _connect(db_url)
    try:
        conn.read_only = True if hasattr(conn, "read_only") else None
    except Exception:
        pass
    try:
        cur = conn.cursor()
        cur.execute(sql)
        if cur.description is None:
            conn.commit()
            return [], []
        columns = [d[0] for d in cur.description]
        rows = cur.fetchmany(limit)
        return columns, rows
    except Exception as e:  # noqa: BLE001
        raise DatabaseConnectionError(str(e)) from e
    finally:
        conn.close()
