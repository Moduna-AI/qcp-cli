from __future__ import annotations

from unittest.mock import Mock

import pytest
from langchain.messages import AIMessage

from qcp import agent as agent_module
from qcp.agent import DatabaseAgent, _query_execution_retry_update
from qcp.db import DatabaseClient
from qcp.errors import DatabaseConnectionError, LLMError
from qcp.llm import ChatModelFactory
from qcp.memory import SchemaMemoryStore


class FakeCompiledAgent:
    def __init__(self, result):
        self.result = result
        self.invocation = None

    def invoke(self, value):
        self.invocation = value
        return self.result


def make_agent(monkeypatch, result):
    compiled_agent = FakeCompiledAgent(result)
    create_agent = Mock(return_value=compiled_agent)
    monkeypatch.setattr(agent_module, "create_agent", create_agent)
    database = Mock(spec=DatabaseClient)
    memory = Mock(spec=SchemaMemoryStore)
    model_factory = Mock(spec=ChatModelFactory)
    model_factory.create.return_value = Mock()
    return DatabaseAgent(database, memory, model_factory), create_agent, compiled_agent


def test_query_returns_exact_tool_result_and_structured_answer(monkeypatch):
    result = {
        "query_result": {
            "sql": "SELECT count(*) AS total FROM users",
            "columns": ["total"],
            "rows": [[7]],
            "truncated": False,
            "executed": True,
        },
        "structured_response": {"answer": "There are 7 users."},
    }
    agent, create_agent, compiled_agent = make_agent(monkeypatch, result)

    response = agent.query("how many users?")

    assert response.query_result.rows == [[7]]
    assert response.answer == "There are 7 users."
    assert create_agent.call_args.kwargs["state_schema"] is agent_module.QcpAgentState
    assert create_agent.call_args.kwargs["middleware"] == [agent_module.require_query_execution]
    assert compiled_agent.invocation["schema_retry_count"] == 0
    assert compiled_agent.invocation["query_execution_retry_count"] == 0


def test_query_requires_an_execute_tool_result(monkeypatch):
    agent, _create_agent, _compiled_agent = make_agent(
        monkeypatch,
        {"structured_response": {"answer": "Unsupported claim"}},
    )
    with pytest.raises(LLMError, match="without producing"):
        agent.query("how many users?")


def test_query_execution_guard_retries_once_when_model_skips_tool():
    state = {
        "messages": [AIMessage(content="There are some users.")],
        "query_result": None,
        "query_execution_retry_count": 0,
    }

    update = _query_execution_retry_update(state)

    assert update is not None
    assert update["jump_to"] == "model"
    assert update["query_execution_retry_count"] == 1
    assert "call execute_read_query" in update["messages"][0].content


def test_query_execution_guard_does_not_interrupt_tool_calls_or_retry_twice():
    tool_call_state = {
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
        ],
        "query_result": None,
        "query_execution_retry_count": 0,
    }
    exhausted_state = {
        "messages": [AIMessage(content="Still no query.")],
        "query_result": None,
        "query_execution_retry_count": 1,
    }

    assert _query_execution_retry_update(tool_call_state) is None
    assert _query_execution_retry_update(exhausted_state) is None


def test_database_errors_are_not_relabelled_as_model_errors(monkeypatch):
    class FailingAgent:
        def invoke(self, _value):
            raise DatabaseConnectionError("offline")

    monkeypatch.setattr(agent_module, "create_agent", Mock(return_value=FailingAgent()))
    database_agent = DatabaseAgent(
        Mock(spec=DatabaseClient),
        Mock(spec=SchemaMemoryStore),
        Mock(spec=ChatModelFactory, create=Mock(return_value=Mock())),
    )

    with pytest.raises(DatabaseConnectionError):
        database_agent.query("how many users?")


def test_insights_supports_schema_only_and_query_grounded_results(monkeypatch):
    result = {
        "query_result": None,
        "structured_response": {"insights": ["One", "Two", "Three"]},
    }
    agent, _create_agent, _compiled_agent = make_agent(monkeypatch, result)

    response = agent.insights()

    assert response.insights == ["One", "Two", "Three"]
    assert response.query_result is None
