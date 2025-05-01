import typing
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from .._protocol import StorageProtocol

SM = typing.TypeVar("SM", bound=DeclarativeBase)


class SQLAlchemyStorage(StorageProtocol[SM]):
    def __init__(self, model: type[SM], get_session: Callable[[], Session]) -> None:
        self.model = model
        self.get_session = get_session

    def get_one(self, **kwargs: typing.Any) -> SM | None:
        statement = select(self.model).filter_by(**kwargs)
        session = self.get_session()
        return session.execute(statement).scalar_one_or_none()

    def create(self, **data: typing.Any) -> SM:
        session = self.get_session()
        instance = self.model(**data)
        session.add(instance)
        session.flush()
        return instance

    def update(self, id: typing.Any, **data: typing.Any) -> SM | None:
        session = self.get_session()
        instance = session.get(self.model, id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        session.add(instance)
        session.flush()
        return instance
