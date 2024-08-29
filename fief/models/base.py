import os

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from fief.settings import settings

TABLE_PREFIX_PLACEHOLDER = "__FIEF__"
GENERATE_MIGRATION = os.environ.get("GENERATE_MIGRATION") == "1"
TABLE_PREFIX = (
    TABLE_PREFIX_PLACEHOLDER if GENERATE_MIGRATION else settings.database_table_prefix
)


def get_prefixed_tablename(name: str) -> str:
    return f"{TABLE_PREFIX}{name}"


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "%(table_name)s_%(column_0_N_name)s_key",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    def __init_subclass__(cls) -> None:
        cls.__tablename__ = get_prefixed_tablename(cls.__tablename__)
        super().__init_subclass__()
