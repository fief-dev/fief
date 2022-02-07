from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, exc, inspect
from sqlalchemy.engine import URL, Engine
from sqlalchemy.schema import CreateSchema

from fief.paths import ALEMBIC_CONFIG_FILE


class AccountDatabaseError(Exception):
    pass


class AccountDatabaseConnectionError(AccountDatabaseError):
    pass


class AccountDatabase:
    def migrate(self, database_url: URL, schema_name: str):
        try:
            engine = self.get_engine(database_url, schema_name)
            with engine.begin() as connection:
                alembic_config = Config(ALEMBIC_CONFIG_FILE, ini_section="account")
                alembic_config.attributes["configure_logger"] = False
                alembic_config.attributes["connection"] = connection
                command.upgrade(alembic_config, "head")
        except exc.OperationalError as e:
            raise AccountDatabaseConnectionError(str(e)) from e

    def get_engine(self, database_url: URL, schema_name: str) -> Engine:
        self._ensure_schema(database_url, schema_name)

        connect_args = {}

        dialect_name = database_url.get_dialect().name
        if dialect_name == "postgresql":
            connect_args["options"] = f"-csearch_path={schema_name}"
        elif dialect_name == "mysql":
            database_url = database_url.set(database=schema_name)
        elif dialect_name == "sqlite":
            database_url = database_url.set(database=f"{schema_name}.db")

        return create_engine(database_url, connect_args=connect_args)

    def _ensure_schema(self, database_url: URL, schema_name: str):
        engine = create_engine(database_url)

        dialect_name = database_url.get_dialect().name
        if dialect_name == "sqlite":
            return

        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        if schema_name not in schemas:
            with engine.begin() as connection:
                connection.execute(CreateSchema(schema_name))
