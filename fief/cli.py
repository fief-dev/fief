import asyncio
import functools
import secrets

import typer
import uvicorn
from alembic import command
from alembic.config import Config
from dramatiq import cli as dramatiq_cli
from pydantic import ValidationError
from sqlalchemy import create_engine

from fief import __version__
from fief.crypto.encryption import generate_key
from fief.paths import ALEMBIC_CONFIG_FILE
from fief.services.password import PasswordValidation
from fief.services.user_manager import InvalidPasswordError, UserAlreadyExistsError


def asyncio_command(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def get_settings():
    from fief.settings import settings

    return settings


app = typer.Typer(help="Commands to manage your Fief instance.")


@app.command("create-admin")
@asyncio_command
async def create_admin(
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
    from fief.services.main_workspace import CreateMainFiefUserError, create_admin
    from fief.services.user_manager import InvalidPasswordError, UserAlreadyExistsError

    try:
        await create_admin(user_email, user_password)
        typer.echo("Main Fief user created")
    except CreateMainFiefUserError as e:
        typer.secho("An error occured", fg="red")
        raise typer.Exit(code=1) from e
    except UserAlreadyExistsError as e:
        typer.secho("User already exists", fg="red")
        raise typer.Exit(code=1) from e
    except InvalidPasswordError as e:
        typer.secho(
            f"Invalid password: {', '.join(map(str, e.messages))}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1) from e


@app.command("create-admin-api-key")
@asyncio_command
async def create_main_admin_api_key(
    token: str = typer.Argument(..., help="The admin API key token"),
):
    """Create a main Fief admin API key."""
    from fief.services.main_workspace import (
        MainFiefAdminApiKeyAlreadyExists,
        create_admin_api_key,
    )

    try:
        await create_admin_api_key(token)
        typer.echo("Main Fief admin API key created")
    except MainFiefAdminApiKeyAlreadyExists as e:
        typer.secho("Main Fief admin API key already exists", fg="red")
        raise typer.Exit(code=1) from e


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

    password_validation = PasswordValidation.validate(user_password)
    if not password_validation.valid:
        typer.secho(
            "Sorry, your password does not meet our complexity requirements. Please re-run with a more complex password.",
            fg=typer.colors.RED,
        )
        for message in password_validation.messages:
            print(f"Error message: {message}")
        raise typer.Exit(code=1)
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
        for key, value in settings.model_dump().items():
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
                    create_admin,
                )

                try:
                    await create_admin(user_email, user_password)
                    typer.echo("Main Fief user created")
                except CreateMainFiefUserError as e:
                    typer.secho(
                        "An error occured while creating main Fief user",
                        fg=typer.colors.RED,
                    )
                    raise typer.Exit(code=1) from e
                except InvalidPasswordError as e:
                    typer.secho(
                        f"Invalid main Fief user password: {', '.join(map(str, e.messages))}",
                        fg=typer.colors.RED,
                    )
                    raise typer.Exit(code=1) from e
                except UserAlreadyExistsError:
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
                    create_admin_api_key,
                )

                try:
                    await create_admin_api_key(token.get_secret_value())
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
