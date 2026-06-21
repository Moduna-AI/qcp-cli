"""Small terminal output helpers (no heavy deps like rich, kept minimal)."""
from __future__ import annotations


def format_table(columns: list[str], rows: list[tuple]) -> str:
    if not columns:
        return "(no output)"
    if not rows:
        return "(0 rows)"

    str_rows = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(c) for c in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    def fmt_row(vals: list[str]) -> str:
        return "  ".join(v.ljust(widths[i]) for i, v in enumerate(vals))

    sep = "  ".join("-" * w for w in widths)
    lines = [fmt_row(columns), sep]
    lines.extend(fmt_row(r) for r in str_rows)
    lines.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(lines)
