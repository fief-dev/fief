from os import path

from sqlalchemy import create_engine

from alembic import command
from alembic.config import Config
from fief.models import Account

alembic_config_file = path.join(
    path.dirname(path.dirname(path.dirname(__file__))), "alembic.ini"
)


class AccountDatabase:
    def migrate(self, account: Account):
        engine = create_engine(account.database_url)
        with engine.begin() as connection:
            alembic_config = Config(alembic_config_file, ini_section="account")
            alembic_config.attributes["connection"] = connection
            command.upgrade(alembic_config, "head")
