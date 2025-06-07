import typing
from collections.abc import AsyncIterable, Callable, Iterable, Sequence

import dishka
from sqlalchemy import URL, Engine, create_engine, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from ._protocol import (
    AsyncStorageProtocol,
    AsyncStorageProvider,
    M,
    StorageProtocol,
    StorageProvider,
)


class SQLAlchemyStorage(StorageProtocol[M]):
    def __init__(self, model: type[M], session: Session) -> None:
        self.model = model
        self.session = session

    def get_one(self, **kwargs: typing.Any) -> M | None:
        statement = select(self.model).filter_by(**kwargs)
        return self.session.execute(statement).scalar_one_or_none()

    def create(self, **data: typing.Any) -> M:
        instance = self.model(**data)
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, id: typing.Any, **data: typing.Any) -> M | None:
        instance = self.session.get(self.model, id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        self.session.add(instance)
        self.session.flush()
        return instance

    def delete(self, id: typing.Any) -> M | None:
        instance = self.session.get(self.model, id)
        if instance is None:
            return None
        self.session.delete(instance)
        self.session.flush()
        return instance


class SQLAlchemyProvider(StorageProvider):
    storage_class: typing.ClassVar[type[SQLAlchemyStorage[typing.Any]]] = (
        SQLAlchemyStorage
    )

    def __init__(
        self, url: str | URL, models: Sequence[type[typing.Any]] | None = None
    ) -> None:
        self.url = url
        super().__init__(models)

    @dishka.provide(scope=dishka.Scope.APP)
    def engine(self) -> Iterable[Engine]:
        engine = create_engine(self.url)
        yield engine
        engine.dispose()

    @dishka.provide(scope=dishka.Scope.REQUEST)
    def session(self, engine: Engine) -> Iterable[Session]:
        with Session(engine) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise
            session.commit()

    def get_model_provider(self, model: type[M]) -> Callable[..., StorageProtocol[M]]:
        def _provide(
            session: Session,
        ) -> StorageProtocol[model]:  # type: ignore[valid-type]
            return self.storage_class(model, session)

        return _provide


class SQLAlchemyAsyncStorage(AsyncStorageProtocol[M]):
    def __init__(self, model: type[M], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_one(self, **kwargs: typing.Any) -> M | None:
        statement = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, **data: typing.Any) -> M:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: typing.Any, **data: typing.Any) -> M | None:
        instance = await self.session.get(self.model, id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, id: typing.Any) -> M | None:
        instance = await self.session.get(self.model, id)
        if instance is None:
            return None
        await self.session.delete(instance)
        await self.session.flush()
        return instance


class SQLAlchemyAsyncProvider(AsyncStorageProvider):
    storage_class: typing.ClassVar[type[SQLAlchemyAsyncStorage[typing.Any]]] = (
        SQLAlchemyAsyncStorage
    )

    def __init__(
        self, url: str | URL, models: Sequence[type[typing.Any]] | None = None
    ) -> None:
        self.url = url
        super().__init__(models)

    @dishka.provide(scope=dishka.Scope.APP)
    async def engine(self) -> AsyncIterable[AsyncEngine]:
        engine = create_async_engine(self.url)
        yield engine
        await engine.dispose()

    @dishka.provide(scope=dishka.Scope.REQUEST)
    async def session(self, engine: AsyncEngine) -> AsyncIterable[AsyncSession]:
        async with AsyncSession(engine) as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            await session.commit()

    def get_model_provider(
        self, model: type[M]
    ) -> Callable[..., AsyncStorageProtocol[M]]:
        def _provide(
            session: AsyncSession,
        ) -> AsyncStorageProtocol[model]:  # type: ignore[valid-type]
            return self.storage_class(model, session)

        return _provide


__all__ = [
    "SQLAlchemyStorage",
    "SQLAlchemyProvider",
    "SQLAlchemyAsyncStorage",
    "SQLAlchemyAsyncProvider",
]
