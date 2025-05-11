from collections.abc import Iterator

import pytest
import sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fief.storage.sqlalchemy import SQLAlchemyStorage


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
