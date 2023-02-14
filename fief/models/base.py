from sqlalchemy.orm import DeclarativeBase

from fief.settings import settings


class MainBase(DeclarativeBase):
    pass


def get_prefixed_tablename(name: str) -> str:
    return f"{settings.workspace_table_prefix}{name}"


class WorkspaceBase(DeclarativeBase):
    def __init_subclass__(cls) -> None:
        cls.__tablename__ = get_prefixed_tablename(cls.__tablename__)
        super().__init_subclass__()
