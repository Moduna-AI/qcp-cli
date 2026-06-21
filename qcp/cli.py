"""qcp - Query Companion: a CLI to query Postgres in natural language."""
from __future__ import annotations

import sys

import click

from . import __version__
from . import config as cfg
from . import db, llm
from .errors import QcpError
from .output import format_table


def _print_err(msg: str) -> None:
    click.secho(msg, fg="red", err=True)


@click.group()
@click.version_option(__version__, prog_name="qcp")
def main() -> None:
    """qcp - your CLI companion for querying Postgres in plain English."""


@main.command()
@click.option("--database-url", "-d", default=None, help="Postgres connection string. Prompted if omitted.")
@click.option("--force", is_flag=True, help="Overwrite existing configuration without asking.")
def init(database_url: str | None, force: bool) -> None:
    """Connect qcp to a Postgres database."""
    existing = cfg.get_db_url()
    if existing and not force:
        if not click.confirm(f"A database is already configured ({_mask(existing)}). Replace it?"):
            click.echo("Keeping existing configuration.")
            return

    if not database_url:
        click.echo("Enter your Postgres connection string, e.g.")
        click.echo("  postgresql://user:password@host:5432/dbname")
        database_url = click.prompt("Database URL", hide_input=True)

    click.echo("Testing connection...")
    db.test_connection(database_url)
    cfg.set_key("database_url", database_url)
    click.secho("✔ Connected and saved.", fg="green")

    if not cfg.get_gemini_api_key():
        click.echo("\nTip: run `qcp auth` next to add your Gemini API key.")


@main.command()
@click.option("--key", "-k", default=None, help="Gemini API key. Prompted if omitted.")
@click.option("--remove", is_flag=True, help="Remove the stored API key.")
@click.option("--skip-validate", is_flag=True, help="Skip validating the key against Gemini.")
@click.option("--model", default=None, help="Override the Gemini model (e.g. gemini-2.5-flash).")
def auth(key: str | None, remove: bool, skip_validate: bool, model: str | None) -> None:
    """Add (or remove) your Gemini API key."""
    if remove:
        cfg.unset_key("gemini_api_key")
        click.secho("✔ Removed stored Gemini API key.", fg="green")
        return

    if model:
        cfg.set_key("gemini_model", model)
        click.echo(f"Using model: {model}")

    if not key:
        click.echo("Get a free Gemini API key at https://aistudio.google.com/apikey")
        key = click.prompt("Gemini API key", hide_input=True)

    if not skip_validate:
        click.echo("Validating key...")
        ok, detail = llm.validate_api_key(key)
        if not ok:
            raise QcpError(
                "That Gemini API key didn't validate "
                f"(model: {llm.get_model()}).\n"
                f"Reason: {detail}\n"
                "Double-check the key, or re-run with --skip-validate to store it anyway."
            )

    cfg.set_key("gemini_api_key", key)
    cfg.set_key("provider", "gemini")
    click.secho("✔ Gemini API key saved.", fg="green")


@main.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--show-sql/--no-show-sql", default=True, help="Print the generated SQL before running it.")
@click.option("--allow-write", is_flag=True, help="Allow non-SELECT statements (use with caution).")
@click.option("--dry-run", is_flag=True, help="Only generate and print SQL, don't execute it.")
def query(question: tuple[str, ...], show_sql: bool, allow_write: bool, dry_run: bool) -> None:
    """Ask a question about your data in plain English.

    Example: qcp query "what were the top 5 products by revenue last month?"
    """
    question_text = " ".join(question)
    db_url = db.require_db_url()

    click.echo("Reading schema...")
    schema = db.get_schema_summary(db_url)

    click.echo("Generating SQL...")
    sql = llm.generate_sql(question_text, schema)

    if show_sql or dry_run:
        click.secho("\n" + sql + "\n", fg="cyan")

    if dry_run:
        return

    columns, rows = db.run_query(db_url, sql, allow_write=allow_write)
    click.echo(format_table(columns, rows))


@main.command()
@click.option("--from-question", default=None, help="Base insights on the results of this question instead of just the schema.")
def insights(from_question: str | None) -> None:
    """Get AI-generated analytics and insights about your database."""
    db_url = db.require_db_url()
    schema = db.get_schema_summary(db_url)

    sample_data = None
    if from_question:
        click.echo("Generating SQL for your question...")
        sql = llm.generate_sql(from_question, schema)
        click.secho("\n" + sql + "\n", fg="cyan")
        columns, rows = db.run_query(db_url, sql)
        sample_data = format_table(columns, rows)
        click.echo(sample_data + "\n")

    click.echo("Generating insights...")
    result = llm.generate_insights(schema, sample_data)
    click.echo("\n" + result)


@main.command()
def status() -> None:
    """Show current qcp configuration."""
    db_url = cfg.get_db_url()
    api_key = cfg.get_gemini_api_key()
    provider = cfg.get_provider()

    click.echo(f"Config file:  {cfg.config_path()}")
    click.echo(f"Database:     {_mask(db_url) if db_url else 'not configured (run `qcp init`)'}")
    click.echo(f"AI provider:  {provider}")
    click.echo(f"Model:        {llm.get_model()}")
    click.echo(f"API key:      {'configured' if api_key else 'not configured (run `qcp auth`)'}")


def _mask(url: str) -> str:
    """Hide credentials in a connection string for display purposes."""
    if "@" not in url:
        return url
    scheme_and_creds, host_part = url.rsplit("@", 1)
    scheme = scheme_and_creds.split("://")[0]
    return f"{scheme}://***@{host_part}"


def run() -> None:
    """Entry point used by the packaged console script."""
    try:
        main(standalone_mode=False)
    except click.exceptions.Abort:
        click.echo("\nAborted.")
        sys.exit(1)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except QcpError as e:
        _print_err(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nAborted.")
        sys.exit(130)


if __name__ == "__main__":
    run()
