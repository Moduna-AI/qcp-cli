"""LangChain tools exposed to the QCP database agent."""

import json
from typing import Any, NotRequired

from langchain.agents import AgentState
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool
from langgraph.types import Command

from qcp.db import DatabaseClient, normalize_read_query
from qcp.errors import SchemaChangedError
from qcp.memory import SchemaMemoryStore
from qcp.models import (
    AnalyzeInsightsInput,
    ExecuteReadQueryInput,
    InsightContext,
    LookupSchemaInput,
    QueryResult,
    SchemaMemoryInput,
    SchemaSnapshot,
)


class QcpAgentState(AgentState):
    """Agent state containing only validated, application-owned artifacts."""

    schema_snapshot: NotRequired[dict[str, Any] | None]
    query_result: NotRequired[dict[str, Any] | None]
    insight_context: NotRequired[dict[str, Any] | None]
    schema_retry_count: NotRequired[int]
    query_execution_retry_count: NotRequired[int]


class DatabaseToolkit:
    """Build dependency-injected LangChain tools for one CLI invocation."""

    def __init__(
        self,
        database: DatabaseClient,
        memory: SchemaMemoryStore,
        *,
        dry_run: bool = False,
    ) -> None:
        """Initialize database and memory dependencies for the tools."""
        self._database = database
        self._memory = memory
        self._dry_run = dry_run

    def build(self) -> list[BaseTool]:
        """Create the schema, memory, query, and insights tools."""
        database = self._database
        memory = self._memory
        dry_run = self._dry_run

        @tool("lookup_schema", args_schema=LookupSchemaInput)
        def lookup_schema(force_refresh: bool, runtime: ToolRuntime[None, QcpAgentState]) -> Command:
            """Read the current public PostgreSQL schema when cache is absent or stale."""
            del force_refresh
            snapshot = database.lookup_schema()
            return _state_command(
                runtime,
                content=f"Current PostgreSQL schema:\n{snapshot.summary()}",
                schema_snapshot=snapshot.model_dump(mode="json"),
            )

        @tool("schema_memory", args_schema=SchemaMemoryInput)
        def schema_memory(operation: str, runtime: ToolRuntime[None, QcpAgentState]) -> Command:
            """Recall a fresh schema snapshot from local memory or store a looked-up snapshot."""
            if operation == "recall":
                snapshot = memory.recall(database.database_id)
                if snapshot is None:
                    return _state_command(runtime, content="Schema memory is missing or older than 24 hours.")
                return _state_command(
                    runtime,
                    content=f"Fresh schema recalled from local memory:\n{snapshot.summary()}",
                    schema_snapshot=snapshot.model_dump(mode="json"),
                )

            raw_snapshot = runtime.state.get("schema_snapshot")
            if raw_snapshot is None:
                return _state_command(runtime, content="No looked-up schema is available to store.")
            snapshot = SchemaSnapshot.model_validate(raw_snapshot)
            memory.store(snapshot)
            return _state_command(runtime, content="Schema snapshot stored in local memory.")

        @tool("execute_read_query", args_schema=ExecuteReadQueryInput)
        def execute_read_query(sql: str, runtime: ToolRuntime[None, QcpAgentState]) -> Command:
            """Execute one PostgreSQL SELECT or WITH query in a read-only transaction."""
            if runtime.state.get("schema_snapshot") is None:
                return _state_command(runtime, content="Schema is required before query execution.")

            if dry_run:
                query_result = QueryResult(sql=normalize_read_query(sql), executed=False)
                return _state_command(
                    runtime,
                    content=json.dumps(query_result.model_dump(mode="json")),
                    query_result=query_result.model_dump(mode="json"),
                )

            try:
                query_result = database.execute_read_query(sql)
            except SchemaChangedError:
                retry_count = runtime.state.get("schema_retry_count", 0)
                if retry_count >= 1:
                    raise
                memory.invalidate(database.database_id)
                return _state_command(
                    runtime,
                    content=(
                        "The cached schema is stale. Call lookup_schema with force_refresh=true, "
                        "store it with schema_memory, then retry this query once."
                    ),
                    schema_snapshot=None,
                    query_result=None,
                    schema_retry_count=1,
                )

            payload = query_result.model_dump(mode="json")
            return _state_command(
                runtime,
                content=json.dumps(payload),
                query_result=payload,
            )

        @tool("analyze_insights", args_schema=AnalyzeInsightsInput)
        def analyze_insights(focus: str | None, runtime: ToolRuntime[None, QcpAgentState]) -> Command:
            """Build grounded facts from schema and optional query results for insight generation."""
            raw_snapshot = runtime.state.get("schema_snapshot")
            if raw_snapshot is None:
                return _state_command(runtime, content="Schema is required before analyzing insights.")
            snapshot = SchemaSnapshot.model_validate(raw_snapshot)
            facts = [
                f"The database snapshot contains {len(snapshot.tables)} tables.",
                "Available tables: " + ", ".join(f"{table.schema_name}.{table.name}" for table in snapshot.tables),
            ]
            if focus:
                facts.append(f"The user's requested analytical focus is: {focus}")
            raw_result = runtime.state.get("query_result")
            if raw_result is not None:
                query_result = QueryResult.model_validate(raw_result)
                facts.extend(
                    [
                        f"The executed query returned {len(query_result.rows)} rows.",
                        "Result columns: " + ", ".join(query_result.columns),
                        "Result sample: " + json.dumps(query_result.model_dump(mode="json")["rows"][:20]),
                    ]
                )
            context = InsightContext(facts=facts)
            payload = context.model_dump(mode="json")
            return _state_command(
                runtime,
                content=json.dumps(payload),
                insight_context=payload,
            )

        return [lookup_schema, schema_memory, execute_read_query, analyze_insights]


def _state_command(runtime: ToolRuntime, content: str, **updates: Any) -> Command:
    """Create a state update containing the required matching tool message."""
    return Command(
        update={
            **updates,
            "messages": [ToolMessage(content=content, tool_call_id=runtime.tool_call_id)],
        }
    )
