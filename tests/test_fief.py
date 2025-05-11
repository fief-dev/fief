import sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fief import Fief
from fief.storage.sqlalchemy import SQLAlchemyProvider, SQLAlchemyStorage
from tests.fixtures import MockProvider, MockStorage, User


class BaseA(DeclarativeBase):
    pass


class ModelA(BaseA):
    __tablename__ = "model_a"
    id: Mapped[int] = mapped_column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True
    )


class ModelB(BaseA):
    __tablename__ = "model_b"
    id: Mapped[int] = mapped_column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True
    )


fief = Fief(
    storage=(
        SQLAlchemyProvider("sqlite:///db_a.db", models=[ModelA]),
        SQLAlchemyProvider("sqlite:///db_b.db", models=[ModelB]),
        MockProvider(models=[User]),
    )
)


def test_storage_provider() -> None:
    with fief:
        storage_a = fief.get_storage(ModelA)
        assert isinstance(storage_a, SQLAlchemyStorage)
        assert storage_a.model is ModelA
        storage_a_bind = storage_a.session.bind
        assert isinstance(storage_a_bind, sqlalchemy.Engine)
        assert str(storage_a_bind.url) == "sqlite:///db_a.db"

        storage_b = fief.get_storage(ModelB)
        assert isinstance(storage_b, SQLAlchemyStorage)
        assert storage_b.model is ModelB
        storage_b_bind = storage_b.session.bind
        assert isinstance(storage_b_bind, sqlalchemy.Engine)
        assert str(storage_b_bind.url) == "sqlite:///db_b.db"

        storage_user = fief.get_storage(User)
        assert isinstance(storage_user, MockStorage)
        assert storage_user.model is User
