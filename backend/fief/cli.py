import asyncio

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
from fief.services.account_creation import (
    CreateGlobalFiefUserError,
    GlobalAccountAlreadyExists,
    create_global_fief_account,
    create_global_fief_user,
)
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


@app.command("create-global-account")
def create_global_account():
    """Create a global Fief account following the environment settings."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(create_global_fief_account())
        typer.echo("Global Fief account created")
    except GlobalAccountAlreadyExists as e:
        typer.echo("Global Fief account already exists")
        raise typer.Exit(code=1) from e


@app.command("create-global-user")
def create_global_user(
    user_email: str = typer.Option(..., help="The admin user email"),
    user_password: str = typer.Option(
        ...,
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        help="The admin user password",
    ),
):
    """Create a global Fief account user."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(create_global_fief_user(user_email, user_password))
        typer.echo("Global Fief user created")
    except CreateGlobalFiefUserError as e:
        typer.echo("An error occured")
        raise typer.Exit(code=1) from e


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
