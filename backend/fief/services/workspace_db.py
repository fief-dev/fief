from typing import Optional, Tuple

from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, exc, inspect
from sqlalchemy.engine import URL, Engine
from sqlalchemy.schema import CreateSchema

from fief.paths import ALEMBIC_CONFIG_FILE


class WorkspaceDatabaseError(Exception):
    pass


class WorkspaceDatabaseConnectionError(WorkspaceDatabaseError):
    def __init__(self, message: str) -> None:
        self.message = message


class WorkspaceDatabase:
    def migrate(self, database_url: URL, schema_name: str) -> str:
        try:
            engine = self.get_engine(database_url, schema_name)
            with engine.begin() as connection:
                config = self._get_alembic_base_config()
                config.attributes["configure_logger"] = False
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
        except exc.OperationalError as e:
            raise WorkspaceDatabaseConnectionError(str(e)) from e

        return self.get_latest_revision()

    def get_engine(self, database_url: URL, schema_name: str) -> Engine:
        self._ensure_schema(database_url, schema_name)

        connect_args = {}

        dialect_name = database_url.get_dialect().name
        if dialect_name == "postgresql":
            connect_args["options"] = f"-csearch_path={schema_name}"
        elif dialect_name == "mysql":
            database_url = database_url.set(database=schema_name)

        return create_engine(database_url, connect_args=connect_args)

    def check_connection(self, database_url: URL) -> Tuple[bool, Optional[str]]:
        try:
            engine = create_engine(database_url)
            with engine.begin():
                return True, None
        except exc.OperationalError as e:
            return False, str(e)

    def get_latest_revision(self) -> str:
        config = self._get_alembic_base_config()
        script = ScriptDirectory.from_config(config)
        with EnvironmentContext(config, script) as environment:
            return str(environment.get_head_revision())

    def _get_alembic_base_config(self) -> Config:
        return Config(ALEMBIC_CONFIG_FILE, ini_section="workspace")

    def _ensure_schema(self, database_url: URL, schema_name: str):
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})

        dialect_name = database_url.get_dialect().name
        if dialect_name == "sqlite":
            return

        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        if schema_name not in schemas:
            with engine.begin() as connection:
                connection.execute(CreateSchema(schema_name))
