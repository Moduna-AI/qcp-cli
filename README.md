# qcp — Query Companion

![PyPI Downloads](https://img.shields.io/pypi/dm/qcp-cli?style=flat-square&label=pip%20installs)
![Downloads](https://img.shields.io/github/downloads/Moduna-AI/qcp/total?style=flat-square&label=downloads)
[![PyPI Downloads](https://img.shields.io/pypi/dm/qcp-cli?style=flat-square&label=pip%20installs)](https://pypi.org/project/qcp-cli)
[![PyPI Version](https://img.shields.io/pypi/v/qcp-cli?style=flat-square)](https://pypi.org/project/qcp-cli)
[![License](https://img.shields.io/github/license/Moduna-AI/qcp?style=flat-square)](LICENSE)
![CI](https://img.shields.io/github/actions/workflow/status/Moduna-AI/qcp-cli/ci.yml?style=flat-square&label=ci)
[![Release](https://img.shields.io/github/v/release/Moduna-AI/qcp-cli?style=flat-square&label=release)](https://github.com/Moduna-AI/qcp/releases)

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

`qcp` is private, secure, safe and runs locally.

## Features

- 🗣️ Ask questions in natural language, get SQL + results
- 🔒 Read-only by default — only `SELECT`/`WITH` statements are executed
- 💡 `qcp insights` — AI-generated analytics suggestions for your schema
- 🧠 Local schema memory with automatic 24-hour refresh
- 🔑 Bring your own Gemini API key (free tier available)
- 🪶 Minimal footprint — single CLI, no servers or daemons

## Install

QCP requires Python 3.14 or newer.

### macOS / Linux (curl)

```bash
curl -L https://github.com/Moduna-AI/qcp-cli/releases/latest/download/qcp-linux-x86_64 -o qcp
chmod +x qcp
sudo mv qcp /usr/local/bin/
```

### macOS (Homebrew)

```bash
brew tap moduna-ai/qcp
brew install moduna-ai/qcp/qcp
```

### Windows (PowerShell)

```powershell
Invoke-WebRequest -Uri "https://github.com/Moduna-AI/qcp-cli/releases/latest/download/qcp-windows-x86_64.exe" -OutFile "qcp.exe"
Move-Item qcp.exe "$env:LOCALAPPDATA\Microsoft\WindowsApps\qcp.exe"
```

### Via pip (any platform)

```bash
pip install qcp-cli
```

### Via uv

```bash
uv tool install qcp-cli
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
Validated schema metadata is cached separately at `~/.qcp/schema.json`; it
never contains credentials or query result rows.
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

## Safety

`qcp` only executes one `SELECT`/`WITH` statement. Validation is backed by a
PostgreSQL read-only transaction, and there is no write override. Always review
generated SQL (shown by default), especially on production databases. A
read-only database role remains recommended as an additional boundary.

## Agent tools

The LangChain agent has four narrow tools: `lookup_schema`, `schema_memory`,
`execute_read_query`, and `analyze_insights`. Schema data is reused for 24
hours, then refreshed automatically. An undefined table, column, or schema
invalidates the cache and permits one refresh-and-retry cycle.

## Development

```bash
git clone https://github.com/Moduna-AI/qcp-cli
cd qcp
uv sync --extra dev
uv run pytest
```

Install the Git hook once with `uv run pre-commit install`. Use
`uv run <command>` for project commands; `uvx` creates an isolated environment
without QCP installed.

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
| Run Ruff checks              | `make lint`                | —                      |

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
