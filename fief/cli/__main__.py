import click
import typer
import typer.core
from pydantic import ValidationError

from fief.cli.quickstart import add_commands as quickstart_add_commands

settings_validation_errors: ValidationError | None = None


class CustomUnknownCommandGroup(typer.core.TyperGroup):
    def resolve_command(self, ctx, args):
        try:
            return super().resolve_command(ctx, args)
        except click.exceptions.UsageError:
            global settings_validation_errors
            if settings_validation_errors:
                message = typer.style("Some settings are invalid or missing.", fg="red")
                typer.echo(f"{message}\n{str(settings_validation_errors)}", err=True)
                raise typer.Exit(code=1) from settings_validation_errors
            raise


app = typer.Typer(
    help="Commands to manage your Fief instance.", cls=CustomUnknownCommandGroup
)
app = quickstart_add_commands(app)

try:
    from fief.cli.admin import add_commands as admin_add_commands

    app = admin_add_commands(app)
except ValidationError as e:
    settings_validation_errors = e

if __name__ == "__main__":
    app()
