from __future__ import annotations

from unittest.mock import Mock

from click.testing import CliRunner

from qcp import cli
from qcp.models import AgentInsightsResponse, AgentQueryResponse, QueryResult


def test_query_prints_sql_table_and_natural_answer(monkeypatch):
    monkeypatch.setenv("QCP_DATABASE_URL", "postgresql://example")
    database_agent = Mock()
    database_agent.query.return_value = AgentQueryResponse(
        query_result=QueryResult(
            sql="SELECT count(*) AS total FROM users",
            columns=["total"],
            rows=[[7]],
        ),
        answer="There are 7 users.",
    )
    monkeypatch.setattr(cli, "_create_agent", Mock(return_value=database_agent))

    result = CliRunner().invoke(cli.main, ["query", "how many users?"])

    assert result.exit_code == 0
    assert "SELECT count(*) AS total FROM users" in result.output
    assert "There are 7 users." in result.output
    assert "7" in result.output


def test_query_hides_sql_but_keeps_table_and_answer(monkeypatch):
    monkeypatch.setenv("QCP_DATABASE_URL", "postgresql://example")
    database_agent = Mock()
    database_agent.query.return_value = AgentQueryResponse(
        query_result=QueryResult(sql="SELECT secret_sql", columns=["value"], rows=[[1]]),
        answer="The value is 1.",
    )
    monkeypatch.setattr(cli, "_create_agent", Mock(return_value=database_agent))

    result = CliRunner().invoke(cli.main, ["query", "value", "--no-show-sql"])

    assert result.exit_code == 0
    assert "secret_sql" not in result.output
    assert "The value is 1." in result.output


def test_dry_run_only_prints_generated_sql(monkeypatch):
    monkeypatch.setenv("QCP_DATABASE_URL", "postgresql://example")
    database_agent = Mock()
    database_agent.query.return_value = AgentQueryResponse(
        query_result=QueryResult(sql="SELECT * FROM users", executed=False),
        answer="Dry run.",
    )
    monkeypatch.setattr(cli, "_create_agent", Mock(return_value=database_agent))

    result = CliRunner().invoke(cli.main, ["query", "users", "--dry-run"])

    assert result.exit_code == 0
    assert "SELECT * FROM users" in result.output
    assert "Dry run." not in result.output


def test_allow_write_option_is_removed():
    result = CliRunner().invoke(cli.main, ["query", "users", "--allow-write"])
    assert result.exit_code != 0
    assert "No such option '--allow-write'" in result.output


def test_insights_print_query_results_when_grounded(monkeypatch):
    monkeypatch.setenv("QCP_DATABASE_URL", "postgresql://example")
    database_agent = Mock()
    database_agent.insights.return_value = AgentInsightsResponse(
        insights=["Revenue rose.", "Monitor churn.", "Compare cohorts."],
        query_result=QueryResult(sql="SELECT revenue FROM metrics", columns=["revenue"], rows=[[100]]),
    )
    monkeypatch.setattr(cli, "_create_agent", Mock(return_value=database_agent))

    result = CliRunner().invoke(cli.main, ["insights", "--from-question", "revenue trend"])

    assert result.exit_code == 0
    assert "SELECT revenue FROM metrics" in result.output
    assert "- Revenue rose." in result.output
