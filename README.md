# qcp — Query Companion

Query your Postgres database in plain English, right from the terminal.

```
$ qcp query "what were the top 5 customers by revenue last month?"
Reading schema...
Generating SQL...

SELECT customer_name, SUM(amount) AS revenue
FROM orders
WHERE order_date >= date_trunc('month', now()) - interval '1 month'
  AND order_date < date_trunc('month', now())
GROUP BY customer_name
ORDER BY revenue DESC
LIMIT 5

customer_name   revenue
--------------  -------
Acme Corp       48210.50
Globex Inc      39120.00
...

(5 rows)
```

`qcp` translates your question into a read-only SQL query using Google
Gemini, runs it against your database, and prints the results. It can also
suggest analytics and insights about your data.

## Features

- 🗣️ Ask questions in natural language, get SQL + results
- 🔒 Read-only by default — only `SELECT`/`WITH` statements are executed
- 💡 `qcp insights` — AI-generated analytics suggestions for your schema
- 🔑 Bring your own Gemini API key (free tier available)
- 🪶 Minimal footprint — single CLI, no servers or daemons

## Install

### macOS / Linux (curl)

```bash
curl -fsSL https://raw.githubusercontent.com/Moduna-AI/qcp/main/scripts/install.sh | bash
```

### macOS (Homebrew)

```bash
brew tap Moduna-AI/qcp
brew install qcp
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/Moduna-AI/qcp/main/scripts/install.ps1 | iex
```

### Via pip (any platform)

```bash
pip install qcp
```

## Quickstart

```bash
# 1. Connect a Postgres database
qcp init

# 2. Add your Gemini API key (https://aistudio.google.com/apikey)
qcp auth

# 3. Ask away
qcp query "how many new signups did we get this week?"

# Or get general insights about your data
qcp insights
```

Running `qcp query` or `qcp insights` without a configured database raises a
clear error and tells you to run `qcp init` first.

## Configuration

`qcp` stores config at `~/.qcp/config.json` (override with `QCP_HOME`).
You can also use environment variables instead of (or to override) the
config file:

| Variable             | Purpose                          |
|----------------------|-----------------------------------|
| `QCP_DATABASE_URL`   | Postgres connection string        |
| `GEMINI_API_KEY`     | Gemini API key                    |

Check current configuration any time with:

```bash
qcp status
```

## Commands

| Command                  | Description                                       |
|---------------------------|---------------------------------------------------|
| `qcp init`                | Connect a Postgres database                       |
| `qcp auth`                | Add/remove your Gemini API key                     |
| `qcp query "<question>"`  | Ask a question, get SQL + results                  |
| `qcp insights`            | Get AI-generated analytics suggestions             |
| `qcp status`              | Show current configuration                         |

Useful flags on `qcp query`:

- `--dry-run` — print the generated SQL without executing it
- `--no-show-sql` — only print results, hide the SQL
- `--allow-write` — allow non-SELECT statements (off by default, not recommended)

## Safety

By default `qcp` only ever executes `SELECT`/`WITH` statements — any other
generated statement is refused before it reaches your database. Always
review generated SQL (shown by default) before trusting the results,
especially on production databases. Consider pointing `qcp` at a read-only
database role.

## Development

```bash
git clone https://github.com/Moduna-AI/qcp
cd qcp
uv sync --extra dev
uv run pytest
```

(Or with plain pip: `pip install -e ".[dev]"` then `pytest`.)

**Note:** if you use `uv`, run things with `uv run <cmd>` (uses this
project's environment), not `uvx <cmd>` (spins up an isolated environment
with *only* that tool, which won't have `qcp` installed and will fail with
`ModuleNotFoundError: No module named 'qcp'`).

### Clean install / clean build

A `Makefile` (plus equivalent standalone shell scripts) is included so you
never get bitten by stale venvs or cached build artifacts:

| Task                       | Make                      | Script                |
|-----------------------------|---------------------------|------------------------|
| Wipe venv/dist/caches        | `make clean`               | `./scripts/clean.sh`   |
| Fresh editable install       | `make install`             | —                      |
| Fresh install + test deps    | `make dev`                 | —                      |
| Clean build (sdist + wheel)  | `make build`                | `./scripts/build.sh`   |
| Clean install, then build    | `make rebuild`              | —                      |
| Run tests                    | `make test`                | —                      |
| Run the CLI from venv        | `make run ARGS="status"`   | —                      |
| Compile-check all files      | `make lint`                | —                      |

`make build` / `./scripts/build.sh` always wipe the tree first, so `dist/`
is never tainted by a previous build. Both are safe to re-run anytime.

## Roadmap (post-MVP)

- Additional LLM providers (OpenAI, Claude, local models)
- MySQL / SQLite support
- Query history and caching
- Saved queries / scheduled reports

## License

MIT — see [LICENSE](LICENSE).

Contributions welcome! Please open an issue or PR.
