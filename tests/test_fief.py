import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fief import Fief
from fief._auth import AuthManager
from fief.methods.password import PasswordMethod, PasswordMethodProvider
from fief.storage.sqlalchemy import SQLAlchemyProvider, SQLAlchemyStorage
from tests.fixtures import MethodModel, MockProvider, MockStorage, UserModel


def test_storage_provider() -> None:
    class Base(DeclarativeBase):
        pass

    class ModelA(Base):
        __tablename__ = "model_a"
        id: Mapped[int] = mapped_column(
            sa.Integer, primary_key=True, autoincrement=True
        )

    class ModelB(Base):
        __tablename__ = "model_b"
        id: Mapped[int] = mapped_column(
            sa.Integer, primary_key=True, autoincrement=True
        )

    fief = Fief(
        storage=(
            SQLAlchemyProvider("sqlite:///db_a.db", models=[ModelA]),
            SQLAlchemyProvider("sqlite:///db_b.db", models=[ModelB]),
            MockProvider(models=[UserModel]),
        ),
        methods=(),
        user_model=UserModel,
    )

    with fief as fief_request:
        storage_a = fief_request.get_storage(ModelA)
        assert isinstance(storage_a, SQLAlchemyStorage)
        assert storage_a.model is ModelA
        storage_a_bind = storage_a.session.bind
        assert isinstance(storage_a_bind, sa.Engine)
        assert str(storage_a_bind.url) == "sqlite:///db_a.db"

        storage_b = fief_request.get_storage(ModelB)
        assert isinstance(storage_b, SQLAlchemyStorage)
        assert storage_b.model is ModelB
        storage_b_bind = storage_b.session.bind
        assert isinstance(storage_b_bind, sa.Engine)
        assert str(storage_b_bind.url) == "sqlite:///db_b.db"

        storage_user = fief_request.get_storage(UserModel)
        assert isinstance(storage_user, MockStorage)
        assert storage_user.model is UserModel

    fief.close()


def test_method_provider() -> None:
    fief = Fief(
        storage=MockProvider(models=[UserModel, MethodModel]),
        methods=(
            PasswordMethodProvider(MethodModel),
            PasswordMethodProvider(MethodModel, name="password2"),
        ),
        user_model=UserModel,
    )

    with fief as fief_request:
        method = fief_request.get_method(PasswordMethod[MethodModel], name="password")
        assert isinstance(method, PasswordMethod)
        assert method.name == "password"
        assert method._storage.model is MethodModel

    fief.close()


def test_auth_manager_provider() -> None:
    fief = Fief(
        storage=MockProvider(models=[UserModel, MethodModel]),
        methods=(PasswordMethodProvider(MethodModel),),
        user_model=UserModel,
    )

    with fief as fief_request:
        manager = fief_request.get_auth_manager()
        assert isinstance(manager, AuthManager)

    fief.close()
