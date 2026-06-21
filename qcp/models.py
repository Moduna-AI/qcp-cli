"""Typed domain models used by the QCP agent and its tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_serializer


class QcpConfig(BaseModel):
    """Validated representation of the persisted QCP configuration."""

    model_config = ConfigDict(extra="ignore")

    database_url: str | None = None
    gemini_api_key: SecretStr | None = None
    provider: Literal["gemini"] = "gemini"
    gemini_model: str = "gemini-2.5-flash"

    @field_serializer("gemini_api_key", when_used="json")
    def serialize_api_key(self, value: SecretStr | None) -> str | None:
        """Persist the actual API key while retaining redacted representations."""
        return value.get_secret_value() if value is not None else None


class SchemaColumn(BaseModel):
    """A PostgreSQL column exposed to the database agent."""

    name: str
    data_type: str
    nullable: bool


class SchemaTable(BaseModel):
    """A PostgreSQL table and its columns."""

    schema_name: str = "public"
    name: str
    columns: list[SchemaColumn]


class SchemaSnapshot(BaseModel):
    """A schema snapshot persisted in local QCP memory."""

    format_version: int = 2
    database_id: str
    captured_at: datetime
    tables: list[SchemaTable]

    def summary(self, max_tables: int = 50) -> str:
        """Return a compact schema representation for the language model."""
        lines: list[str] = []
        for table in self.tables[:max_tables]:
            columns = ", ".join(f"{column.name} {column.data_type}" for column in table.columns)
            lines.append(f"- {table.schema_name}.{table.name}({columns})")
        if len(self.tables) > max_tables:
            lines.append(f"... and {len(self.tables) - max_tables} more tables")
        return "\n".join(lines) if lines else "(no tables found in 'public' schema)"


class QueryResult(BaseModel):
    """The exact SQL and rows returned by the read-query tool."""

    sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    truncated: bool = False
    executed: bool = True


class InsightContext(BaseModel):
    """Grounded facts supplied to the model for insight generation."""

    facts: list[str]


class QueryNarrative(BaseModel):
    """Structured natural-language response from the query agent."""

    answer: str = Field(description="A concise answer grounded only in the executed query result.")


class InsightsNarrative(BaseModel):
    """Structured natural-language response from the insights agent."""

    insights: list[str] = Field(min_length=3, max_length=6)


class AgentQueryResponse(BaseModel):
    """Application-level response returned to the CLI query command."""

    query_result: QueryResult
    answer: str


class AgentInsightsResponse(BaseModel):
    """Application-level response returned to the CLI insights command."""

    insights: list[str]
    query_result: QueryResult | None = None


class LookupSchemaInput(BaseModel):
    """Input for the schema lookup tool."""

    force_refresh: bool = Field(default=False, description="Ignore cached state and query PostgreSQL again.")


class SchemaMemoryInput(BaseModel):
    """Input for the local schema-memory tool."""

    operation: Literal["recall", "store"]


class ExecuteReadQueryInput(BaseModel):
    """Input for the read-only query execution tool."""

    sql: str = Field(description="One PostgreSQL SELECT or WITH query without multiple statements.")


class AnalyzeInsightsInput(BaseModel):
    """Input for the grounded insights tool."""

    focus: str | None = Field(default=None, description="Optional analytical focus supplied by the user.")
