from os import path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateSchema

from alembic import command
from alembic.config import Config
from fief.models import Account

alembic_config_file = path.join(
    path.dirname(path.dirname(path.dirname(__file__))), "alembic.ini"
)


class AccountDatabase:
    def migrate(self, account: Account):
        schema_name = self._create_schema(account)
        engine = self._get_schema_engine(account, schema_name)
        with engine.begin() as connection:
            alembic_config = Config(alembic_config_file, ini_section="account")
            alembic_config.attributes["connection"] = connection
            command.upgrade(alembic_config, "head")

    def _create_schema(self, account: Account) -> str:
        schema_name = str(account.id)
        engine = create_engine(account.get_database_url(asyncio=False))
        with engine.begin() as connection:
            if engine.dialect.name != "sqlite":
                connection.execute(CreateSchema(schema_name))
        return schema_name

    def _get_schema_engine(self, account: Account, schema_name: str) -> Engine:
        database_url = account.get_database_url(asyncio=False)
        connect_args = {}

        if database_url.startswith("postgresql://"):
            connect_args["options"] = f"-csearch_path={schema_name}"

        return create_engine(database_url, connect_args=connect_args)
