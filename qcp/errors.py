"""Application exceptions converted to clean messages at the CLI boundary."""


class QcpError(Exception):
    """Base error for all QCP CLI failures."""


class NoDatabaseConfiguredError(QcpError):
    """Raised when a command needs a database but none is configured."""

    def __init__(self) -> None:
        """Initialize the actionable configuration error."""
        super().__init__(
            "No database is configured.\n"
            "Run `qcp init` to connect a Postgres database, "
            "or set the QCP_DATABASE_URL environment variable."
        )


class NoApiKeyConfiguredError(QcpError):
    """Raised when a command needs Gemini but no key is configured."""

    def __init__(self, provider: str = "gemini") -> None:
        """Initialize the actionable API-key error."""
        super().__init__(
            f"No API key configured for provider '{provider}'.\n"
            f"Run `qcp auth` to add your {provider.title()} API key, "
            f"or set the GEMINI_API_KEY environment variable."
        )


class DatabaseConnectionError(QcpError):
    """Raised for PostgreSQL connection or execution failures."""

    def __init__(self, detail: str) -> None:
        """Initialize the database error with driver details."""
        super().__init__(f"Could not connect to the database: {detail}")


class LLMError(QcpError):
    """Raised when Gemini or the LangChain agent fails."""

    def __init__(self, detail: str) -> None:
        """Initialize the AI provider error."""
        super().__init__(f"AI provider error: {detail}")


class UnsafeQueryError(QcpError):
    """Raised when SQL is not one read-only statement."""

    def __init__(self, statement: str) -> None:
        """Initialize the query safety error."""
        super().__init__(
            "Refusing to run a non-read-only statement generated from your "
            f"question:\n  {statement}\n"
            "qcp only executes one SELECT or WITH query."
        )


class SchemaChangedError(QcpError):
    """Raised when cached schema metadata no longer matches PostgreSQL."""
