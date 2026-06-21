class QcpError(Exception):
    """Base error for all qcp CLI failures. Caught at the CLI boundary
    and printed as a clean message (no traceback) with exit code 1.
    """


class NoDatabaseConfiguredError(QcpError):
    def __init__(self) -> None:
        super().__init__(
            "No database is configured.\n"
            "Run `qcp init` to connect a Postgres database, "
            "or set the QCP_DATABASE_URL environment variable."
        )


class NoApiKeyConfiguredError(QcpError):
    def __init__(self, provider: str = "gemini") -> None:
        super().__init__(
            f"No API key configured for provider '{provider}'.\n"
            f"Run `qcp auth` to add your {provider.title()} API key, "
            f"or set the GEMINI_API_KEY environment variable."
        )


class DatabaseConnectionError(QcpError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Could not connect to the database: {detail}")


class LLMError(QcpError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"AI provider error: {detail}")


class UnsafeQueryError(QcpError):
    def __init__(self, statement: str) -> None:
        super().__init__(
            "Refusing to run a non-read-only statement generated from your "
            f"question:\n  {statement}\n"
            "qcp only executes SELECT queries. Use --allow-write to override "
            "(not recommended)."
        )
