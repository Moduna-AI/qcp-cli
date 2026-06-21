from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

from langchain.messages import AIMessage
from langchain.tools import ToolRuntime
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from qcp.db import DatabaseClient
from qcp.errors import SchemaChangedError
from qcp.memory import SchemaMemoryStore
from qcp.models import QueryResult, SchemaColumn, SchemaSnapshot, SchemaTable
from qcp.tools import DatabaseToolkit, QcpAgentState


def make_snapshot() -> SchemaSnapshot:
    return SchemaSnapshot(
        database_id="database-a",
        captured_at=datetime.now(UTC),
        tables=[SchemaTable(name="users", columns=[SchemaColumn(name="id", data_type="integer", nullable=False)])],
    )


def make_runtime(state=None) -> ToolRuntime:
    return ToolRuntime(
        state=state or {},
        context=None,
        config={},
        stream_writer=lambda _value: None,
        tool_call_id="tool-call",
        store=None,
    )


def make_tools(*, dry_run=False):
    database = Mock(spec=DatabaseClient)
    database.database_id = "database-a"
    memory = Mock(spec=SchemaMemoryStore)
    tools = {tool.name: tool for tool in DatabaseToolkit(database, memory, dry_run=dry_run).build()}
    return database, memory, tools


def test_all_four_tools_are_exposed_with_pydantic_schemas():
    _database, _memory, tools = make_tools()
    assert set(tools) == {"lookup_schema", "schema_memory", "execute_read_query", "analyze_insights"}
    assert all(tool.args_schema is not None for tool in tools.values())


def test_tool_node_injects_runtime_with_explicit_pydantic_schema():
    database, memory, tools = make_tools()
    memory.recall.return_value = None
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "schema_memory",
                        "args": {"operation": "recall"},
                        "id": "tool-call",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }

    graph_builder = StateGraph(QcpAgentState)
    graph_builder.add_node("tools", ToolNode(list(tools.values())))
    graph_builder.set_entry_point("tools")
    graph_builder.set_finish_point("tools")

    result = graph_builder.compile().invoke(state)

    memory.recall.assert_called_once_with(database.database_id)
    assert "missing" in result["messages"][-1].content


def test_schema_lookup_and_memory_update_agent_state():
    database, memory, tools = make_tools()
    snapshot = make_snapshot()
    database.lookup_schema.return_value = snapshot

    lookup_command = tools["lookup_schema"].func(force_refresh=True, runtime=make_runtime())
    state = {"schema_snapshot": lookup_command.update["schema_snapshot"]}
    store_command = tools["schema_memory"].func(operation="store", runtime=make_runtime(state))

    memory.store.assert_called_once_with(snapshot)
    assert "stored" in store_command.update["messages"][0].content


def test_dry_run_records_sql_without_database_execution():
    database, _memory, tools = make_tools(dry_run=True)
    runtime = make_runtime({"schema_snapshot": make_snapshot().model_dump(mode="json")})

    command = tools["execute_read_query"].func(sql="SELECT * FROM users;", runtime=runtime)

    result = QueryResult.model_validate(command.update["query_result"])
    assert result.sql == "SELECT * FROM users"
    assert result.executed is False
    database.execute_read_query.assert_not_called()


def test_stale_schema_invalidates_cache_and_allows_only_one_retry():
    database, memory, tools = make_tools()
    database.execute_read_query.side_effect = SchemaChangedError("undefined column")
    state = {"schema_snapshot": make_snapshot().model_dump(mode="json"), "schema_retry_count": 0}

    command = tools["execute_read_query"].func(sql="SELECT missing FROM users", runtime=make_runtime(state))

    memory.invalidate.assert_called_once_with("database-a")
    assert command.update["schema_retry_count"] == 1
    assert command.update["schema_snapshot"] is None

    state["schema_retry_count"] = 1
    try:
        tools["execute_read_query"].func(sql="SELECT missing FROM users", runtime=make_runtime(state))
    except SchemaChangedError:
        pass
    else:
        raise AssertionError("second schema mismatch must fail")


def test_insights_tool_uses_schema_and_exact_query_result():
    _database, _memory, tools = make_tools()
    state = {
        "schema_snapshot": make_snapshot().model_dump(mode="json"),
        "query_result": QueryResult(sql="SELECT count(*) FROM users", columns=["count"], rows=[[4]]).model_dump(
            mode="json"
        ),
    }

    command = tools["analyze_insights"].func(focus="growth", runtime=make_runtime(state))

    facts = command.update["insight_context"]["facts"]
    assert any("4" in fact for fact in facts)
    assert any("growth" in fact for fact in facts)
