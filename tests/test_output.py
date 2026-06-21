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


def test_format_table_uses_expanded_records_when_result_is_too_wide():
    long_path = "gs://bucket/" + "x" * 100

    out = format_table(
        ["id", "gcs_run_path", "error_message"],
        [("run_123", long_path, "Embedding artifact contains an invalid vector")],
        max_width=60,
    )

    assert "-[ RECORD 1 ]" in out
    assert "gcs_run_path" in out
    assert out.count("x") == 100
    assert all(len(line) <= 60 for line in out.splitlines())
    assert "(1 row)" in out


def test_format_table_expanded_records_preserve_multiple_rows_and_multiline_values():
    out = format_table(
        ["identifier", "message"],
        [("first", "line one\nline two"), ("second", "y" * 80)],
        max_width=40,
    )

    assert "-[ RECORD 1 ]" in out
    assert "-[ RECORD 2 ]" in out
    assert "line one" in out
    assert "line two" in out
    assert out.count("y") == 80
    assert "(2 rows)" in out


def test_format_table_expanded_records_do_not_truncate_long_column_names():
    column_name = "exceptionally_long_column_name"

    out = format_table([column_name], [("line one\nline two",)], max_width=40)

    compact_output = "".join(line.split(" | ", maxsplit=1)[0].strip() for line in out.splitlines()[1:-2])
    assert column_name in compact_output
    assert "line one" in out
    assert "line two" in out
