from qcp.output import format_table


def test_format_table_empty_rows():
    assert format_table(["id", "name"], []) == "(0 rows)"


def test_format_table_no_columns():
    assert format_table([], []) == "(no output)"


def test_format_table_basic():
    out = format_table(["id", "name"], [(1, "Alice"), (2, "Bob")])
    assert "id" in out and "name" in out
    assert "Alice" in out and "Bob" in out
    assert "(2 rows)" in out


def test_format_table_handles_none():
    out = format_table(["id", "name"], [(1, None)])
    assert "(1 row)" in out
