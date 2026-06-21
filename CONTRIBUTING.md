# Contributing to qcp

Thanks for considering a contribution! qcp aims to stay minimal, so please
keep PRs focused.

## Setup

```bash
git clone https://github.com/Moduna-AI/qcp-cli
cd qcp
uv sync --extra dev
uv run pre-commit install
uv run pytest
```

## Guidelines

- New LLM providers should implement `ChatModelFactory` rather than branching
  provider logic across the codebase.
- Any code path that executes SQL must go through `DatabaseClient.execute_read_query`,
  which enforces the read-only check and transaction.
- Add or update tests in `tests/` for any behavior change.
- Run `uv run ruff check .`, `uv run ruff format --check .`, and
  `uv run pytest` before opening a PR.

## Reporting issues

Please include your `qcp --version`, OS, and the command you ran (redact
your database URL / API key).
