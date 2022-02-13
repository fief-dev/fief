import typer
import uvicorn
from alembic import command
from alembic.config import Config
from dramatiq import cli as dramatiq_cli
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from fief import __version__
from fief.models import Account
from fief.paths import ALEMBIC_CONFIG_FILE
from fief.services.account_db import AccountDatabase
from fief.settings import settings

app = typer.Typer()


@app.command()
def info():
    """Show current Fief version and settings."""
    typer.secho(f"Fief version: {__version__}", bold=True)
    typer.secho(f"Settings", bold=True)
    for key, value in settings.dict().items():
        typer.echo(f"{key}: {value}")


@app.command("migrate-global")
def migrate_global():
    """Apply database migrations to the global database."""
    engine = create_engine(settings.get_database_url(False))
    with engine.begin() as connection:
        alembic_config = Config(ALEMBIC_CONFIG_FILE, ini_section="global")
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")


@app.command("migrate-accounts")
def migrate_accounts():
    """Apply database migrations to each account database."""
    engine = create_engine(settings.get_database_url(False))
    Session = sessionmaker(engine)
    with Session() as session:
        account_db = AccountDatabase()
        accounts = select(Account)
        for [account] in session.execute(accounts):
            assert isinstance(account, Account)
            typer.secho(f"Migrating {account.name}", bold=True)
            account_db.migrate(
                account.get_database_url(False), account.get_schema_name()
            )


@app.command("run-server")
def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    migrate: bool = typer.Option(
        True,
        help="Run the migrations on global and accounts databases before starting.",
    ),
):
    """Run the Fief backend server."""
    if migrate:
        migrate_global()
        migrate_accounts()
    uvicorn.run("fief.app:app", host=host, port=port)


@app.command(
    "run-worker",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def run_worker(ctx: typer.Context):
    """
    Run the Fief worker.

    Just forwards the options to the Dramatiq CLI.
    """
    parser = dramatiq_cli.make_argument_parser()
    args = parser.parse_args(ctx.args + ["fief.worker"])
    dramatiq_cli.main(args)


if __name__ == "__main__":
    app()
