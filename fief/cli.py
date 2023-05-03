import asyncio
import functools
import secrets

import typer
import uvicorn
from alembic import command
from alembic.config import Config
from dramatiq import cli as dramatiq_cli
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from fief import __version__
from fief.crypto.encryption import generate_key
from fief.logger import init_logger
from fief.paths import ALEMBIC_CONFIG_FILE
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)

init_logger()


def asyncio_command(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def get_settings():
    from fief.settings import settings

    return settings


workspaces = typer.Typer(help="Commands to manage workspaces.")


@workspaces.command()
@asyncio_command
async def list():
    """List all workspaces and their number of users."""
    from fief.services.workspaces import get_workspaces_stats

    stats = await get_workspaces_stats()

    table = Table()
    table.add_column("Name")
    table.add_column("Reachable")
    table.add_column("Database")
    table.add_column("Database type")
    table.add_column("Migration revision")
    table.add_column("Nb. users")
    for stat in stats:
        table.add_row(
            stat.workspace.name,
            "✅" if stat.reachable else "❌",
            "External" if stat.external_db else "Main",
            stat.workspace.database_type if stat.external_db else None,
            stat.workspace.alembic_revision,
            str(stat.nb_users) if stat.reachable else None,
            style="red" if not stat.reachable else None,
        )
    console = Console()
    console.print(table)


@workspaces.command("migrate")
def migrate_workspaces():
    """Apply database migrations to each workspace database."""
    from fief.models import Workspace

    settings = get_settings()

    url, connect_args = settings.get_database_connection_parameters(False)
    engine = create_engine(url, connect_args=connect_args)
    Session = sessionmaker(engine)
    with Session() as session:
        workspace_db = WorkspaceDatabase()
        latest_revision = workspace_db.get_latest_revision()
        workspaces = select(Workspace).where(
            Workspace.alembic_revision != latest_revision
        )
        for [workspace] in session.execute(workspaces):
            assert isinstance(workspace, Workspace)
            typer.secho(f"Migrating {workspace.name}... ", bold=True, nl=False)
            try:
                alembic_revision = workspace_db.migrate(
                    workspace.get_database_connection_parameters(False),
                    workspace.get_schema_name(),
                )
                workspace.alembic_revision = alembic_revision
                session.add(workspace)
                session.commit()
                typer.secho("Done!")
            except WorkspaceDatabaseConnectionError:
                typer.secho("Failed!", fg="red", err=True)


@workspaces.command("init-email-templates")
@asyncio_command
async def init_email_templates():
    """Ensure email templates are initialized in each workspace."""
    from fief.models import Workspace
    from fief.services.email_template.initializer import init_email_templates

    settings = get_settings()

    url, connect_args = settings.get_database_connection_parameters(False)
    engine = create_engine(url, connect_args=connect_args)
    Session = sessionmaker(engine)
    with Session() as session:
        workspace_db = WorkspaceDatabase()
        latest_revision = workspace_db.get_latest_revision()
        workspaces = select(Workspace).where(
            Workspace.alembic_revision == latest_revision
        )
        for [workspace] in session.execute(workspaces):
            assert isinstance(workspace, Workspace)
            typer.secho(f"Checking {workspace.name}... ", bold=True, nl=False)
            try:
                await init_email_templates(workspace)
                typer.secho("Done!")
            except (ConnectionError, DBAPIError):
                typer.secho("Failed!", fg="red", err=True)


@workspaces.command("init-themes")
@asyncio_command
async def init_themes():
    """Ensure themes are initialized in each workspace."""
    from fief.models import Workspace
    from fief.services.theme import init_workspace_default_theme

    settings = get_settings()

    url, connect_args = settings.get_database_connection_parameters(False)
    engine = create_engine(url, connect_args=connect_args)
    Session = sessionmaker(engine)
    with Session() as session:
        workspace_db = WorkspaceDatabase()
        latest_revision = workspace_db.get_latest_revision()
        workspaces = select(Workspace).where(
            Workspace.alembic_revision == latest_revision
        )
        for [workspace] in session.execute(workspaces):
            assert isinstance(workspace, Workspace)
            typer.secho(f"Checking {workspace.name}... ", bold=True, nl=False)
            try:
                await init_workspace_default_theme(workspace)
                typer.secho("Done!")
            except (ConnectionError, DBAPIError):
                typer.secho("Failed!", fg="red", err=True)


@workspaces.command("create-main")
@asyncio_command
async def create_main_workspace():
    """Create a main Fief workspace following the environment settings."""
    from fief.services.main_workspace import (
        MainWorkspaceAlreadyExists,
        create_main_fief_workspace,
    )

    try:
        await create_main_fief_workspace()
        typer.echo("Main Fief workspace created")
    except MainWorkspaceAlreadyExists as e:
        typer.secho("Main Fief workspace already exists", fg="red")
        raise typer.Exit(code=1) from e


@workspaces.command("create-main-user")
@asyncio_command
async def create_main_user(
    user_email: str = typer.Option(..., help="The admin user email"),
    user_password: str = typer.Option(
        ...,
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        help="The admin user password",
    ),
):
    """Create a main Fief workspace user."""
    from fief.services.main_workspace import (
        CreateMainFiefUserError,
        create_main_fief_user,
    )

    try:
        await create_main_fief_user(user_email, user_password)
        typer.echo("Main Fief user created")
    except CreateMainFiefUserError as e:
        typer.secho("An error occured", fg="red")
        raise typer.Exit(code=1) from e
    except UserAlreadyExists as e:
        typer.secho("User already exists", fg="red")
        raise typer.Exit(code=1) from e
    except InvalidPasswordException as e:
        typer.secho(f"Invalid password: {e.reason}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e


@workspaces.command("create-main-admin-api-key")
@asyncio_command
async def create_main_admin_api_key(
    token: str = typer.Argument(..., help="The admin API key token")
):
    """Create a main Fief admin API key."""
    from fief.services.main_workspace import (
        MainFiefAdminApiKeyAlreadyExists,
        create_main_fief_admin_api_key,
    )

    try:
        await create_main_fief_admin_api_key(token)
        typer.echo("Main Fief admin API key created")
    except MainFiefAdminApiKeyAlreadyExists as e:
        typer.secho("Main Fief admin API key already exists", fg="red")
        raise typer.Exit(code=1) from e


app = typer.Typer(help="Commands to manage your Fief instance.")
app.add_typer(workspaces, name="workspaces")


@app.command()
def quickstart(
    user_email: str = typer.Option(..., prompt=True, help="The admin user email"),
    user_password: str = typer.Option(
        ...,
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        help="The admin user password",
    ),
    docker: bool = typer.Option(
        False,
        help="Show the Docker command to run the Fief server with required environment variables.",
    ),
    port: int = typer.Option(
        8000, help="Port on which you want to expose the Fief server."
    ),
    host: str = typer.Option(
        "localhost", help="Host on which you want to expose the Fief server."
    ),
    ssl: bool = typer.Option(
        False,
        help="Whether the Fief server will be served over SSL. For local development, it'll likely be false.",
    ),
):
    """Generate secrets and environment variables to help users getting started quickly."""
    typer.secho(
        "⚠️  Be sure to save the generated secrets somewhere safe for subsequent runs. Otherwise, you may lose access to the data.",
        bold=True,
        fg="red",
        err=True,
    )

    environment_variables = {
        "SECRET": secrets.token_urlsafe(64),
        "FIEF_CLIENT_ID": secrets.token_urlsafe(),
        "FIEF_CLIENT_SECRET": secrets.token_urlsafe(),
        "ENCRYPTION_KEY": generate_key().decode("utf-8"),
        "PORT": port,
        "ROOT_DOMAIN": f"{host}:{port}",
        "FIEF_DOMAIN": f"{host}:{port}",
        "FIEF_MAIN_USER_EMAIL": user_email,
        "FIEF_MAIN_USER_PASSWORD": user_password,
    }
    if not ssl:
        environment_variables.update(
            {
                "CSRF_COOKIE_SECURE": False,
                "SESSION_DATA_COOKIE_SECURE": False,
                "USER_LOCALE_COOKIE_SECURE": False,
                "LOGIN_HINT_COOKIE_SECURE": False,
                "LOGIN_SESSION_COOKIE_SECURE": False,
                "REGISTRATION_SESSION_COOKIE_SECURE": False,
                "SESSION_COOKIE_SECURE": False,
                "FIEF_ADMIN_SESSION_COOKIE_SECURE": False,
            }
        )

    if docker:
        parts = [
            "docker run",
            "--name fief-server",
            f"-p {port}:{port}",
            "-d",
            *[
                f'-e "{name}={value}"'
                for (name, value) in environment_variables.items()
            ],
            "ghcr.io/fief-dev/fief:latest",
        ]
        typer.echo(" \\\n  ".join(parts))
    else:
        for name, value in environment_variables.items():
            typer.echo(f"{typer.style(name, bold=True)}={value}")


@app.command()
def info():
    """Show current Fief version and settings."""
    try:
        settings = get_settings()

        typer.secho(f"Fief version: {__version__}", bold=True)
        typer.secho("Settings", bold=True)
        for key, value in settings.dict().items():
            typer.echo(f"{key}: {value}")
    except ValidationError as e:
        typer.secho(
            "❌ Some environment variables are missing or invalid.", bold=True, fg="red"
        )
        typer.secho(
            "Run 'fief quickstart' to help you generate the secrets.", bold=True
        )
        for error in e.errors():
            typer.secho(error)
        raise typer.Exit(code=1) from e


@app.command("migrate")
def migrate_main():
    """Apply database migrations to the main database."""
    settings = get_settings()

    url, connect_args = settings.get_database_connection_parameters(False)
    engine = create_engine(url, connect_args=connect_args)
    with engine.begin() as connection:
        alembic_config = Config(ALEMBIC_CONFIG_FILE, ini_section="main")
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")


@app.command("run-server")
def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    migrate: bool = typer.Option(
        True,
        help="Run the migrations on main and workspaces databases before starting.",
    ),
    create_main_workspace: bool = typer.Option(
        True, help="Create the main Fief workspace before starting if needed."
    ),
    create_main_user: bool = typer.Option(
        True, help="Create the main Fief user before starting if needed."
    ),
    create_main_admin_api_key: bool = typer.Option(
        True, help="Create the main Fief admin API key before starting if needed."
    ),
):
    """Run the Fief server."""

    async def _pre_run_server():
        if migrate:
            migrate_main()
            migrate_workspaces()

        if create_main_workspace:
            from fief.services.main_workspace import (
                MainWorkspaceAlreadyExists,
                create_main_fief_workspace,
            )

            try:
                await create_main_fief_workspace()
                typer.echo("Main Fief workspace created")
            except MainWorkspaceAlreadyExists:
                typer.echo("Main Fief workspace already exists")

        if create_main_user:
            settings = get_settings()
            user_email = settings.fief_main_user_email
            user_password = (
                settings.fief_main_user_password.get_secret_value()
                if settings.fief_main_user_password
                else None
            )
            if user_email is None:
                typer.secho(
                    "Main Fief user email not provided in settings. Skipping its creation.",
                    fg=typer.colors.YELLOW,
                )
            else:
                from fief.services.main_workspace import (
                    CreateMainFiefUserError,
                    create_main_fief_user,
                )

                try:
                    await create_main_fief_user(user_email, user_password)
                    typer.echo("Main Fief user created")
                except CreateMainFiefUserError as e:
                    typer.secho(
                        "An error occured while creating main Fief user",
                        fg=typer.colors.RED,
                    )
                    raise typer.Exit(code=1) from e
                except InvalidPasswordException as e:
                    typer.secho(
                        f"Invalid main Fief user password: {e.reason}",
                        fg=typer.colors.RED,
                    )
                    raise typer.Exit(code=1) from e
                except UserAlreadyExists:
                    typer.echo("Main Fief user already exists")

        if create_main_admin_api_key:
            settings = get_settings()
            token = settings.fief_main_admin_api_key
            if token is None:
                typer.secho(
                    "Main Fief admin API key not provided in settings. Skipping its creation.",
                    fg=typer.colors.YELLOW,
                )
            else:
                from fief.services.main_workspace import (
                    MainFiefAdminApiKeyAlreadyExists,
                    create_main_fief_admin_api_key,
                )

                try:
                    await create_main_fief_admin_api_key(token.get_secret_value())
                    typer.echo("Main Fief admin API key created")
                except MainFiefAdminApiKeyAlreadyExists:
                    typer.secho("Main Fief admin API key already exists")

    asyncio.run(_pre_run_server())
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
    args = parser.parse_args(ctx.args + ["fief.worker", "-ffief.scheduler:schedule"])
    dramatiq_cli.main(args)


if __name__ == "__main__":
    app()
