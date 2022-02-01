from os import path

from sqlalchemy import create_engine, exc
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateSchema

from alembic import command
from alembic.config import Config

alembic_config_file = path.join(
    path.dirname(path.dirname(path.dirname(__file__))), "alembic.ini"
)


class AccountDatabaseError(Exception):
    pass


class AccountDatabaseConnectionError(AccountDatabaseError):
    pass


class AccountDatabase:
    def migrate(self, database_url: str, schema_name: str):
        try:
            self._create_schema(database_url, schema_name)
            engine = self._get_schema_engine(database_url, schema_name)
            with engine.begin() as connection:
                alembic_config = Config(alembic_config_file, ini_section="account")
                alembic_config.attributes["connection"] = connection
                command.upgrade(alembic_config, "head")
        except exc.OperationalError as e:
            raise AccountDatabaseConnectionError(str(e)) from e

    def _create_schema(self, database_url: str, schema_name: str):
        engine = create_engine(database_url)
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema_name))

    def _get_schema_engine(self, database_url: str, schema_name: str) -> Engine:
        connect_args = {}

        if database_url.startswith("postgresql://"):
            connect_args["options"] = f"-csearch_path={schema_name}"

        return create_engine(database_url, connect_args=connect_args)
