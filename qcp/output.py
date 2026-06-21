"""Small terminal output helpers kept independent from the agent layer."""

from __future__ import annotations

import shutil
import textwrap
from collections.abc import Sequence
from typing import Any

DEFAULT_TERMINAL_WIDTH = 120
MIN_TERMINAL_WIDTH = 40
COLUMN_SEPARATOR = "  "
EXPANDED_SEPARATOR = " | "


def format_table(
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    max_width: int | None = None,
) -> str:
    """Format query results for the current terminal width.

    Compact results use a conventional horizontal table. Results that cannot
    fit the terminal switch to an expanded record layout so long values remain
    readable without truncation.

    Args:
        columns: Column names in result order.
        rows: Query result rows.
        max_width: Optional deterministic width override, primarily for tests.

    Returns:
        A terminal-friendly representation including the result row count.
    """
    if not columns:
        return "(no output)"
    if not rows:
        return "(0 rows)"

    terminal_width = max(
        MIN_TERMINAL_WIDTH,
        max_width or shutil.get_terminal_size(fallback=(DEFAULT_TERMINAL_WIDTH, 24)).columns,
    )
    str_rows = [[_stringify(value) for value in row] for row in rows]
    widths = [len(c) for c in columns]
    for row in str_rows:
        for index, value in enumerate(row[: len(widths)]):
            widths[index] = max(widths[index], len(value))

    table_width = sum(widths) + len(COLUMN_SEPARATOR) * (len(widths) - 1)
    contains_multiline_value = any("\n" in value for row in str_rows for value in row)
    if table_width > terminal_width or contains_multiline_value:
        return _format_expanded(columns, str_rows, terminal_width)

    def fmt_row(vals: list[str]) -> str:
        padded_values = [*vals[: len(widths)], *([""] * max(0, len(widths) - len(vals)))]
        return COLUMN_SEPARATOR.join(value.ljust(widths[index]) for index, value in enumerate(padded_values))

    separator = COLUMN_SEPARATOR.join("-" * width for width in widths)
    lines = [fmt_row(list(columns)), separator]
    lines.extend(fmt_row(row) for row in str_rows)
    lines.append(f"\n{_row_count(len(rows))}")
    return "\n".join(lines)


def _stringify(value: Any) -> str:
    """Convert a result value to one safe display string."""
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\r", "\n")


def _format_expanded(columns: Sequence[str], rows: Sequence[Sequence[str]], max_width: int) -> str:
    """Render wide results as wrapped, vertically expanded records."""
    label_width = min(max(len(column) for column in columns), max_width // 3)
    value_width = max(1, max_width - label_width - len(EXPANDED_SEPARATOR))
    lines: list[str] = []

    for row_number, row in enumerate(rows, start=1):
        if lines:
            lines.append("")
        lines.append(f"-[ RECORD {row_number} ]".ljust(max_width, "-"))
        padded_row = [*row[: len(columns)], *([""] * max(0, len(columns) - len(row)))]
        for column, value in zip(columns, padded_row, strict=True):
            wrapped_column = _wrap_value(column, label_width)
            wrapped_value = _wrap_value(value, value_width)
            part_count = max(len(wrapped_column), len(wrapped_value))
            for part_index in range(part_count):
                label_part = wrapped_column[part_index] if part_index < len(wrapped_column) else ""
                value_part = wrapped_value[part_index] if part_index < len(wrapped_value) else ""
                lines.append(f"{label_part.ljust(label_width)}{EXPANDED_SEPARATOR}{value_part}")

    lines.append(f"\n{_row_count(len(rows))}")
    return "\n".join(lines)


def _wrap_value(value: str, width: int) -> list[str]:
    """Wrap long and multiline values without dropping their content."""
    if not value:
        return [""]
    wrapped_lines: list[str] = []
    for logical_line in value.split("\n"):
        wrapped_lines.extend(
            textwrap.wrap(
                logical_line,
                width=width,
                replace_whitespace=False,
                drop_whitespace=False,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [""]
        )
    return wrapped_lines


def _row_count(row_count: int) -> str:
    """Return the conventional result-count footer."""
    return f"({row_count} row{'s' if row_count != 1 else ''})"
