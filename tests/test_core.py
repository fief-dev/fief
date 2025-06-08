import dataclasses
import uuid
from collections.abc import AsyncGenerator, Generator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_asyncio
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fief import (
    Fief,
    FiefAsync,
    MissingIdentifierFieldsException,
    UserAlreadyExistsException,
)
from fief._core import FiefAsyncRequest, FiefRequest
from fief.methods.password import (
    PasswordAsyncMethod,
    PasswordAsyncMethodProvider,
    PasswordMethod,
    PasswordMethodModelData,
    PasswordMethodProvider,
)
from fief.storage.sqlalchemy import (
    SQLAlchemyAsyncProvider,
    SQLAlchemyAsyncStorage,
    SQLAlchemyProvider,
    SQLAlchemyStorage,
)
from tests.fixtures import (
    MethodModel,
    MockAsyncProvider,
    MockAsyncStorage,
    MockProvider,
    MockStorage,
    UserModel,
)


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
        storage=SQLAlchemyProvider("sqlite:///db.db"),
        methods=(),
        user_model=UserModel,
    )

    with fief as fief_request:
        storage_a = fief_request.get_storage(ModelA)
        assert isinstance(storage_a, SQLAlchemyStorage)
        assert storage_a.model is ModelA
        storage_a_bind = storage_a.session.bind
        assert isinstance(storage_a_bind, sa.Engine)
        assert str(storage_a_bind.url) == "sqlite:///db.db"

        storage_b = fief_request.get_storage(ModelB)
        assert isinstance(storage_b, SQLAlchemyStorage)
        assert storage_b.model is ModelB
        storage_b_bind = storage_b.session.bind
        assert isinstance(storage_b_bind, sa.Engine)
        assert str(storage_b_bind.url) == "sqlite:///db.db"

    fief.close()


@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_async_storage_provider(anyio_backend: str) -> None:
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

    fief = FiefAsync(
        storage=SQLAlchemyAsyncProvider("sqlite+aiosqlite:///db.db"),
        methods=(),
        user_model=UserModel,
    )

    async with fief as fief_request:
        storage_a = await fief_request.get_storage(ModelA)
        assert isinstance(storage_a, SQLAlchemyAsyncStorage)
        assert storage_a.model is ModelA
        storage_a_bind = storage_a.session.bind
        assert isinstance(storage_a_bind, sa_asyncio.AsyncEngine)
        assert str(storage_a_bind.url) == "sqlite+aiosqlite:///db.db"

        storage_b = await fief_request.get_storage(ModelB)
        assert isinstance(storage_b, SQLAlchemyAsyncStorage)
        assert storage_b.model is ModelB
        storage_b_bind = storage_b.session.bind
        assert isinstance(storage_b_bind, sa_asyncio.AsyncEngine)
        assert str(storage_b_bind.url) == "sqlite+aiosqlite:///db.db"

    await fief.close()


def test_multiple_storage_providers() -> None:
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


@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_async_multiple_storage_providers(anyio_backend: str) -> None:
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

    fief = FiefAsync(
        storage=(
            SQLAlchemyAsyncProvider("sqlite+aiosqlite:///db_a.db", models=[ModelA]),
            SQLAlchemyAsyncProvider("sqlite+aiosqlite:///db_b.db", models=[ModelB]),
            MockAsyncProvider(models=[UserModel]),
        ),
        methods=(),
        user_model=UserModel,
    )

    async with fief as fief_request:
        storage_a = await fief_request.get_storage(ModelA)
        assert isinstance(storage_a, SQLAlchemyAsyncStorage)
        assert storage_a.model is ModelA
        storage_a_bind = storage_a.session.bind
        assert isinstance(storage_a_bind, sa_asyncio.AsyncEngine)
        assert str(storage_a_bind.url) == "sqlite+aiosqlite:///db_a.db"

        storage_b = await fief_request.get_storage(ModelB)
        assert isinstance(storage_b, SQLAlchemyAsyncStorage)
        assert storage_b.model is ModelB
        storage_b_bind = storage_b.session.bind
        assert isinstance(storage_b_bind, sa_asyncio.AsyncEngine)
        assert str(storage_b_bind.url) == "sqlite+aiosqlite:///db_b.db"

        storage_user = await fief_request.get_storage(UserModel)
        assert isinstance(storage_user, MockAsyncStorage)
        assert storage_user.model is UserModel

    await fief.close()


def test_method_provider() -> None:
    fief = Fief(
        storage=MockProvider(),
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


@pytest.mark.anyio
async def test_async_method_provider() -> None:
    fief = FiefAsync(
        storage=MockAsyncProvider(),
        methods=(
            PasswordAsyncMethodProvider(MethodModel),
            PasswordAsyncMethodProvider(MethodModel, name="password2"),
        ),
        user_model=UserModel,
    )

    async with fief as fief_request:
        method = await fief_request.get_method(
            PasswordAsyncMethod[MethodModel], name="password"
        )
        assert isinstance(method, PasswordAsyncMethod)
        assert method.name == "password"
        assert method._storage.model is MethodModel

    await fief.close()


@dataclasses.dataclass
class PasswordMethodModel:
    name: str
    user_id: str
    data: PasswordMethodModelData
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@pytest.fixture
def fief() -> Fief[UserModel]:
    return Fief(
        storage=MockProvider(),
        methods=(PasswordMethodProvider(PasswordMethodModel),),
        user_model=UserModel,
    )


@pytest.fixture
def fief_request(fief: Fief[UserModel]) -> Generator[FiefRequest[UserModel]]:
    with fief as fief_request:
        yield fief_request


@pytest.fixture
def fief_async() -> FiefAsync[UserModel]:
    return FiefAsync(
        storage=MockAsyncProvider(),
        methods=(PasswordAsyncMethodProvider(PasswordMethodModel),),
        user_model=UserModel,
    )


@pytest.fixture
async def fief_request_async(
    fief_async: FiefAsync[UserModel],
) -> AsyncGenerator[FiefAsyncRequest[UserModel]]:
    async with fief_async as fief_request:
        yield fief_request


class TestSignup:
    def test_missing_identifier_fields(
        self, fief_request: FiefRequest[UserModel]
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            fief_request.signup(
                PasswordMethod[PasswordMethodModel],
                {"password": "richard"},
                name="Aliénor",
            )

    def test_user_already_exists(self, fief_request: FiefRequest[UserModel]) -> None:
        user_storage = fief_request.get_storage(UserModel)
        user_storage.create(email="alienor@aquitaine.duchy")

        with pytest.raises(UserAlreadyExistsException):
            fief_request.signup(
                PasswordMethod[PasswordMethodModel],
                {"password": "richard"},
                email="alienor@aquitaine.duchy",
            )

    def test_valid(self, fief_request: FiefRequest[UserModel]) -> None:
        user = fief_request.signup(
            PasswordMethod[PasswordMethodModel],
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert user.id is not None
        assert user.email == "alienor@aquitaine.duchy"

        password_method = fief_request.get_method(PasswordMethod[PasswordMethodModel])
        password_method_model = password_method._storage.get_one(
            user_id=user.id, name=password_method.name
        )
        assert password_method_model is not None
        assert password_method_model.user_id == user.id


class TestSignin:
    def test_missing_identifier_fields(
        self, fief_request: FiefRequest[UserModel]
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            fief_request.signin(
                PasswordMethod[PasswordMethodModel],
                {"password": "richard"},
                name="Aliénor",
            )

    def test_non_existing_user(self, fief_request: FiefRequest[UserModel]) -> None:
        user = fief_request.signin(
            PasswordMethod[PasswordMethodModel],
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert user is None

    def test_invalid_authentication(self, fief_request: FiefRequest[UserModel]) -> None:
        user_storage = fief_request.get_user_storage()
        user = user_storage.create(email="alienor@aquitaine.duchy")
        password_method = fief_request.get_method(PasswordMethod[PasswordMethodModel])
        password_method.enroll(user.id, {"password": "richard"})

        authenticated_user = fief_request.signin(
            PasswordMethod[PasswordMethodModel],
            {"password": "wrongpassword"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is None

    def test_valid_authentication(self, fief_request: FiefRequest[UserModel]) -> None:
        user_storage = fief_request.get_user_storage()
        user = user_storage.create(email="alienor@aquitaine.duchy")
        password_method = fief_request.get_method(PasswordMethod[PasswordMethodModel])
        password_method.enroll(user.id, {"password": "richard"})

        authenticated_user = fief_request.signin(
            PasswordMethod[PasswordMethodModel],
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id


@pytest.mark.anyio
class TestAsyncSignup:
    async def test_missing_identifier_fields(
        self, fief_request_async: FiefAsyncRequest[UserModel]
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            await fief_request_async.signup(
                PasswordAsyncMethod[PasswordMethodModel],
                {"password": "richard"},
                name="Aliénor",
            )

    async def test_user_already_exists(
        self, fief_request_async: FiefAsyncRequest[UserModel]
    ) -> None:
        user_storage = await fief_request_async.get_storage(UserModel)
        await user_storage.create(email="alienor@aquitaine.duchy")

        with pytest.raises(UserAlreadyExistsException):
            await fief_request_async.signup(
                PasswordAsyncMethod[PasswordMethodModel],
                {"password": "richard"},
                email="alienor@aquitaine.duchy",
            )

    async def test_valid(self, fief_request_async: FiefAsyncRequest[UserModel]) -> None:
        user = await fief_request_async.signup(
            PasswordAsyncMethod[PasswordMethodModel],
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert user.id is not None
        assert user.email == "alienor@aquitaine.duchy"

        password_method = await fief_request_async.get_method(
            PasswordAsyncMethod[PasswordMethodModel]
        )
        password_method_model = await password_method._storage.get_one(
            user_id=user.id, name=password_method.name
        )
        assert password_method_model is not None
        assert password_method_model.user_id == user.id


@pytest.mark.anyio
class TestAsyncSignin:
    async def test_missing_identifier_fields(
        self, fief_request_async: FiefAsyncRequest[UserModel]
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            await fief_request_async.signin(
                PasswordAsyncMethod[PasswordMethodModel],
                {"password": "richard"},
                name="Aliénor",
            )

    async def test_non_existing_user(
        self, fief_request_async: FiefAsyncRequest[UserModel]
    ) -> None:
        user = await fief_request_async.signin(
            PasswordAsyncMethod[PasswordMethodModel],
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert user is None

    async def test_invalid_authentication(
        self, fief_request_async: FiefAsyncRequest[UserModel]
    ) -> None:
        user_storage = await fief_request_async.get_user_storage()
        user = await user_storage.create(email="alienor@aquitaine.duchy")
        password_method = await fief_request_async.get_method(
            PasswordAsyncMethod[PasswordMethodModel]
        )
        await password_method.enroll(user.id, {"password": "richard"})

        authenticated_user = await fief_request_async.signin(
            PasswordAsyncMethod[PasswordMethodModel],
            {"password": "wrongpassword"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is None

    async def test_valid_authentication(
        self, fief_request_async: FiefAsyncRequest[UserModel]
    ) -> None:
        user_storage = await fief_request_async.get_user_storage()
        user = await user_storage.create(email="alienor@aquitaine.duchy")
        password_method = await fief_request_async.get_method(
            PasswordAsyncMethod[PasswordMethodModel]
        )
        await password_method.enroll(user.id, {"password": "richard"})

        authenticated_user = await fief_request_async.signin(
            PasswordAsyncMethod[PasswordMethodModel],
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
