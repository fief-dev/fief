from collections.abc import AsyncIterator, Iterator

import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fief.storage.sqlalchemy import SQLAlchemyAsyncStorage, SQLAlchemyStorage


class Base(DeclarativeBase):
    pass


class Model(Base):
    __tablename__ = "model"
    id: Mapped[int] = mapped_column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(sqlalchemy.String, nullable=False)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def storage(session: Session) -> SQLAlchemyStorage[Model]:
    return SQLAlchemyStorage(Model, session)


def test_storage(storage: SQLAlchemyStorage[Model]) -> None:
    # Create a new instance
    instance = storage.create(name="test")
    assert instance.id is not None
    assert instance.name == "test"

    # Retrieve the instance
    retrieved_instance = storage.get_one(id=instance.id)
    assert retrieved_instance is not None
    assert retrieved_instance.id == instance.id
    assert retrieved_instance.name == "test"

    # Update the instance
    updated_instance = storage.update(instance.id, name="updated")
    assert updated_instance is not None
    assert updated_instance.id == instance.id
    assert updated_instance.name == "updated"

    # Update a non-existing instance
    non_existing_instance = storage.update(999, name="non-existing")
    assert non_existing_instance is None


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def async_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        async with AsyncSession(connection) as session:
            yield session
    await engine.dispose()


@pytest.fixture
async def async_storage(async_session: AsyncSession) -> SQLAlchemyAsyncStorage[Model]:
    return SQLAlchemyAsyncStorage(Model, async_session)


@pytest.mark.anyio()
async def test_async_storage(async_storage: SQLAlchemyAsyncStorage[Model]) -> None:
    # Create a new instance
    instance = await async_storage.create(name="test")
    assert instance.id is not None
    assert instance.name == "test"

    # Retrieve the instance
    retrieved_instance = await async_storage.get_one(id=instance.id)
    assert retrieved_instance is not None
    assert retrieved_instance.id == instance.id
    assert retrieved_instance.name == "test"

    # Update the instance
    updated_instance = await async_storage.update(instance.id, name="updated")
    assert updated_instance is not None
    assert updated_instance.id == instance.id
    assert updated_instance.name == "updated"

    # Update a non-existing instance
    non_existing_instance = await async_storage.update(999, name="non-existing")
    assert non_existing_instance is None
