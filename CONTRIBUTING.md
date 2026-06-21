# Contributing to qcp

Thanks for considering a contribution! qcp aims to stay minimal, so please
keep PRs focused.

## Setup

```bash
git clone https://github.com/your-org/qcp
cd qcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,postgres]"
pytest
```

## Guidelines

- Keep the CLI dependency-light (currently just `click`).
- New LLM providers should implement the same small interface as `qcp/llm.py`
  (`generate_sql`, `generate_insights`, `validate_api_key`) rather than
  branching logic across the codebase.
- Any code path that executes SQL must go through `db.run_query`, which
  enforces the read-only check.
- Add or update tests in `tests/` for any behavior change.
- Run `pytest` before opening a PR.

## Reporting issues

Please include your `qcp --version`, OS, and the command you ran (redact
your database URL / API key).
