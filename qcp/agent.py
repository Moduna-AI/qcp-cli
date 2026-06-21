"""LangChain database-agent orchestration for QCP commands."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, TypeVar

from langchain.agents import create_agent
from langchain.agents.middleware import after_model
from langchain.messages import HumanMessage
from langgraph.runtime import Runtime
from pydantic import BaseModel, ValidationError

from qcp.db import DatabaseClient
from qcp.errors import LLMError, QcpError
from qcp.llm import ChatModelFactory
from qcp.memory import SchemaMemoryStore
from qcp.models import (
    AgentInsightsResponse,
    AgentQueryResponse,
    InsightsNarrative,
    QueryNarrative,
    QueryResult,
)
from qcp.tools import DatabaseToolkit, QcpAgentState

SYSTEM_PROMPT = """You are QCP, a PostgreSQL data analyst for non-developers.
Use tools sequentially and ground every claim in tool output.
Always call schema_memory with operation=recall first. If it misses, call lookup_schema,
then schema_memory with operation=store. Never invent tables, columns, SQL results, or insights.
Only execute one SELECT or WITH query. Never request or attempt writes, DDL, or multiple statements.
If execute_read_query reports stale schema, refresh, store, and retry exactly once.
Keep final answers concise and understandable to a non-developer.
"""

QUERY_EXECUTION_RETRY_PROMPT = (
    "Your previous response did not execute a query. QCP requires SQL and exact rows for every query command. "
    "Use the schema already loaded, call execute_read_query now, and only then return the concise answer."
)

NarrativeModel = TypeVar("NarrativeModel", bound=BaseModel)


class AgentInvoker(Protocol):
    """Minimal invocation interface implemented by compiled LangChain graphs."""

    def invoke(self, value: dict[str, Any]) -> Mapping[str, Any]:
        """Invoke the compiled graph with an agent-state update."""


def _query_execution_retry_update(state: QcpAgentState) -> dict[str, Any] | None:
    """Return a one-time corrective state update when the model skips execution."""
    if state.get("query_result") is not None or state.get("query_execution_retry_count", 0) >= 1:
        return None
    messages = state.get("messages", [])
    if not messages or getattr(messages[-1], "tool_calls", None):
        return None
    return {
        "messages": [HumanMessage(content=QUERY_EXECUTION_RETRY_PROMPT)],
        "query_execution_retry_count": 1,
        "jump_to": "model",
    }


@after_model(state_schema=QcpAgentState, can_jump_to=["model"])
def require_query_execution(state: QcpAgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Give Gemini one corrective turn when it answers without executing SQL."""
    del runtime
    return _query_execution_retry_update(state)


class DatabaseAgent:
    """Coordinate LangChain agents while preserving exact tool artifacts."""

    def __init__(
        self,
        database: DatabaseClient,
        memory: SchemaMemoryStore,
        model_factory: ChatModelFactory,
    ) -> None:
        """Initialize the agent with abstract infrastructure dependencies."""
        self._database = database
        self._memory = memory
        self._model_factory = model_factory

    def query(self, question: str, *, dry_run: bool = False) -> AgentQueryResponse:
        """Answer a natural-language question using one read-only SQL query."""
        agent = create_agent(
            model=self._model_factory.create(),
            tools=DatabaseToolkit(self._database, self._memory, dry_run=dry_run).build(),
            system_prompt=SYSTEM_PROMPT,
            state_schema=QcpAgentState,
            response_format=QueryNarrative,
            middleware=[require_query_execution],
        )
        prompt = (
            f"Question: {question}\n"
            "Find the schema, produce one PostgreSQL query, call execute_read_query, "
            "then return a concise answer."
        )
        if dry_run:
            prompt += " This is a dry run: validate and record the SQL with the tool, but do not claim any data result."
        result = self._invoke(agent, prompt)
        raw_query_result = result.get("query_result")
        if raw_query_result is None:
            raise LLMError("the agent finished without producing a SQL query result")
        narrative = self._validate_narrative(QueryNarrative, result.get("structured_response"))
        return AgentQueryResponse(
            query_result=QueryResult.model_validate(raw_query_result),
            answer=narrative.answer,
        )

    def insights(self, from_question: str | None = None) -> AgentInsightsResponse:
        """Generate schema-grounded or query-grounded analytical suggestions."""
        agent = create_agent(
            model=self._model_factory.create(),
            tools=DatabaseToolkit(self._database, self._memory).build(),
            system_prompt=SYSTEM_PROMPT,
            state_schema=QcpAgentState,
            response_format=InsightsNarrative,
        )
        if from_question:
            prompt = (
                f"Generate insights for this focus: {from_question}\n"
                "Load the schema, create and execute one relevant read query, call analyze_insights, "
                "then return 3-6 grounded insights."
            )
        else:
            prompt = (
                "Load the schema, call analyze_insights without executing a query, "
                "then return 3-6 concrete analyses the user could run next."
            )
        result = self._invoke(agent, prompt)
        narrative = self._validate_narrative(InsightsNarrative, result.get("structured_response"))
        raw_query_result = result.get("query_result")
        query_result = QueryResult.model_validate(raw_query_result) if raw_query_result is not None else None
        return AgentInsightsResponse(insights=narrative.insights, query_result=query_result)

    @staticmethod
    def _invoke(agent: AgentInvoker, prompt: str) -> dict[str, Any]:
        """Invoke LangChain and normalize provider failures into QCP errors."""
        try:
            result = agent.invoke(
                {
                    "messages": [{"role": "user", "content": prompt}],
                    "schema_snapshot": None,
                    "query_result": None,
                    "insight_context": None,
                    "schema_retry_count": 0,
                    "query_execution_retry_count": 0,
                }
            )
        except QcpError:
            raise
        except Exception as error:
            raise LLMError(str(error)) from error
        return dict(result)

    @staticmethod
    def _validate_narrative(model: type[NarrativeModel], value: object) -> NarrativeModel:
        """Convert invalid structured model output into a user-facing AI error."""
        try:
            return model.model_validate(value)
        except ValidationError as error:
            raise LLMError("the agent returned an invalid structured response") from error
