from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection

from fief.db import AsyncEngine
from fief.paths import ALEMBIC_CONFIG_FILE


def _get_alembic_config(connection: Connection) -> Config:
    config = Config(ALEMBIC_CONFIG_FILE)
    config.attributes["connection"] = connection
    return config


async def migrate_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:

        def _run_upgrade(connection):
            alembic_config = _get_alembic_config(connection)
            command.upgrade(alembic_config, "head")

        await connection.run_sync(_run_upgrade)
