from sqlalchemy.orm import DeclarativeBase

TABLE_PREFIX_PLACEHOLDER = "__FIEF__"


def get_prefixed_tablename(name: str) -> str:
    return f"{TABLE_PREFIX_PLACEHOLDER}{name}"


class Base(DeclarativeBase):
    def __init_subclass__(cls) -> None:
        cls.__tablename__ = get_prefixed_tablename(cls.__tablename__)
        super().__init_subclass__()
