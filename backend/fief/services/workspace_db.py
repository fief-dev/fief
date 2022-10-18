from contextlib import contextmanager
from typing import Generator, Optional, Tuple

from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, exc, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateSchema

from fief.db.types import DatabaseConnectionParameters
from fief.paths import ALEMBIC_CONFIG_FILE


class WorkspaceDatabaseError(Exception):
    pass


class WorkspaceDatabaseConnectionError(WorkspaceDatabaseError):
    def __init__(self, message: str) -> None:
        self.message = message


class WorkspaceDatabase:
    def migrate(
        self,
        database_connection_parameters: DatabaseConnectionParameters,
        schema_name: str,
    ) -> str:
        try:
            self._ensure_schema(database_connection_parameters, schema_name)
            with self._get_engine(
                database_connection_parameters, schema_name
            ) as engine:
                with engine.begin() as connection:
                    config = self._get_alembic_base_config()
                    config.attributes["configure_logger"] = False
                    config.attributes["connection"] = connection
                    command.upgrade(config, "head")
        except exc.OperationalError as e:
            raise WorkspaceDatabaseConnectionError(str(e)) from e
        return self.get_latest_revision()

    def check_connection(
        self, database_connection_parameters: DatabaseConnectionParameters
    ) -> Tuple[bool, Optional[str]]:
        with self._get_engine(database_connection_parameters) as engine:
            try:
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

    @contextmanager
    def _get_engine(
        self,
        database_connection_parameters: DatabaseConnectionParameters,
        schema_name: str | None = None,
    ) -> Generator[Engine, None, None]:

        database_url, connect_args = database_connection_parameters

        if schema_name is not None:
            dialect_name = database_url.get_dialect().name
            if dialect_name == "postgresql":
                connect_args["options"] = f"-csearch_path={schema_name}"
            elif dialect_name == "mysql":
                database_url = database_url.set(database=schema_name)

        engine = create_engine(database_url, connect_args=connect_args)

        yield engine

        engine.dispose()

    def _ensure_schema(
        self,
        database_connection_parameters: DatabaseConnectionParameters,
        schema_name: str,
    ):
        with self._get_engine(database_connection_parameters) as engine:
            dialect_name = engine.dialect.name
            if dialect_name == "sqlite":
                return

            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            if schema_name not in schemas:
                with engine.begin() as connection:
                    connection.execute(CreateSchema(schema_name))
