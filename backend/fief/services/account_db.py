import asyncio
from os import path
from typing import Optional

from sqlalchemy import create_engine, exc, inspect, select
from sqlalchemy.engine import URL, Engine
from sqlalchemy.schema import CreateSchema

from alembic import command
from alembic.config import Config
from fief.db import global_async_session_maker
from fief.managers import AccountManager
from fief.models import Account

alembic_config_file = path.join(
    path.dirname(path.dirname(path.dirname(__file__))), "alembic.ini"
)


class AccountDatabaseError(Exception):
    pass


class AccountDatabaseConnectionError(AccountDatabaseError):
    pass


class AccountDatabase:
    def migrate(self, database_url: URL, schema_name: str):
        try:
            self._ensure_schema(database_url, schema_name)
            engine = self._get_engine(database_url, schema_name)
            with engine.begin() as connection:
                alembic_config = Config(alembic_config_file, ini_section="account")
                alembic_config.attributes["connection"] = connection
                command.upgrade(alembic_config, "head")
        except exc.OperationalError as e:
            raise AccountDatabaseConnectionError(str(e)) from e

    def _ensure_schema(self, database_url: URL, schema_name: str):
        engine = create_engine(database_url)
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        if schema_name not in schemas:
            with engine.begin() as connection:
                connection.execute(CreateSchema(schema_name))

    def _get_engine(self, database_url: URL, schema_name: str) -> Engine:
        connect_args = {}

        dialect_name = database_url.get_dialect().name
        if dialect_name == "postgresql":
            connect_args["options"] = f"-csearch_path={schema_name}"
        elif dialect_name == "mysql":
            database_url = database_url.set(database=schema_name)

        return create_engine(database_url, connect_args=connect_args)


def migrate_account_db(account_database: AccountDatabase, account: Account):
    account_database.migrate(account.get_database_url(False), account.get_schema_name())


async def migrate_accounts():
    account_database = AccountDatabase()
    async with global_async_session_maker() as session:
        account_manager = AccountManager(session)
        accounts = await account_manager.list(select(Account))
        for account in accounts:
            migrate_account_db(account_database, account)


if __name__ == "__main__":
    asyncio.run(migrate_accounts())
