import typer
from pydantic import ValidationError

from fief.cli.quickstart import add_commands as quickstart_add_commands

app = typer.Typer(help="Commands to manage your Fief instance.")
app = quickstart_add_commands(app)

try:
    from fief.cli.admin import add_commands as admin_add_commands

    app = admin_add_commands(app)
except ValidationError:
    pass

if __name__ == "__main__":
    app()
