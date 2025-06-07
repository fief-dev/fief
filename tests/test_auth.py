import dataclasses
import uuid

import pytest

from fief._auth import (
    AsyncAuthManager,
    AuthManager,
    MissingIdentifierFieldsException,
    UserAlreadyExistsException,
)
from fief.methods.password import (
    PasswordAsyncMethod,
    PasswordMethod,
    PasswordMethodModelData,
)
from tests.fixtures import MockAsyncStorage, MockStorage, UserModel


@dataclasses.dataclass
class PasswordMethodModel:
    name: str
    user_id: str
    data: PasswordMethodModelData
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@pytest.fixture
def password_method() -> PasswordMethod[PasswordMethodModel]:
    return PasswordMethod(storage=MockStorage(PasswordMethodModel))


@pytest.fixture
def storage() -> MockStorage[UserModel]:
    return MockStorage(UserModel)


@pytest.fixture
def auth_manager(storage: MockStorage[UserModel]) -> AuthManager[UserModel]:
    return AuthManager(UserModel, storage)


@pytest.fixture
def password_async_method() -> PasswordAsyncMethod[PasswordMethodModel]:
    return PasswordAsyncMethod(storage=MockAsyncStorage(PasswordMethodModel))


@pytest.fixture
def async_storage() -> MockAsyncStorage[UserModel]:
    return MockAsyncStorage(UserModel)


@pytest.fixture
def async_auth_manager(
    async_storage: MockAsyncStorage[UserModel],
) -> AsyncAuthManager[UserModel]:
    return AsyncAuthManager(UserModel, async_storage)


class TestSignup:
    def test_missing_identifier_fields(
        self,
        auth_manager: AuthManager[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            auth_manager.signup(
                password_method, {"password": "richard"}, name="Aliénor"
            )

    def test_user_already_exists(
        self,
        auth_manager: AuthManager[UserModel],
        storage: MockStorage[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        storage.create(email="alienor@aquitaine.duchy")

        with pytest.raises(UserAlreadyExistsException):
            auth_manager.signup(
                password_method,
                {"password": "richard"},
                email="alienor@aquitaine.duchy",
            )

    def test_valid(
        self,
        auth_manager: AuthManager[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = auth_manager.signup(
            password_method, {"password": "richard"}, email="alienor@aquitaine.duchy"
        )
        assert user.id is not None
        assert user.email == "alienor@aquitaine.duchy"

        password_method_model = password_method._storage.get_one(
            user_id=user.id, name=password_method.name
        )
        assert password_method_model is not None
        assert password_method_model.user_id == user.id


class TestSignin:
    def test_missing_identifier_fields(
        self,
        auth_manager: AuthManager[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            auth_manager.signin(
                password_method, {"password": "richard"}, name="Aliénor"
            )

    def test_non_existing_user(
        self,
        auth_manager: AuthManager[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = auth_manager.signin(
            password_method, {"password": "richard"}, email="alienor@aquitaine.duchy"
        )
        assert user is None

    def test_invalid_authentication(
        self,
        auth_manager: AuthManager[UserModel],
        storage: MockStorage[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = storage.create(email="alienor@aquitaine.duchy")
        password_method.enroll(user.id, {"password": "richard"})

        authenticated_user = auth_manager.signin(
            password_method,
            {"password": "wrongpassword"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is None

    def test_valid_authentication(
        self,
        auth_manager: AuthManager[UserModel],
        storage: MockStorage[UserModel],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = storage.create(email="alienor@aquitaine.duchy")
        password_method.enroll(user.id, {"password": "richard"})

        authenticated_user = auth_manager.signin(
            password_method, {"password": "richard"}, email="alienor@aquitaine.duchy"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id


@pytest.mark.anyio
class TestAsyncSignup:
    async def test_missing_identifier_fields(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            await async_auth_manager.signup(
                password_async_method, {"password": "richard"}, name="Aliénor"
            )

    async def test_user_already_exists(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        async_storage: MockAsyncStorage[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        await async_storage.create(email="alienor@aquitaine.duchy")

        with pytest.raises(UserAlreadyExistsException):
            await async_auth_manager.signup(
                password_async_method,
                {"password": "richard"},
                email="alienor@aquitaine.duchy",
            )

    async def test_valid(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        user = await async_auth_manager.signup(
            password_async_method,
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert user.id is not None
        assert user.email == "alienor@aquitaine.duchy"

        password_method_model = await password_async_method._storage.get_one(
            user_id=user.id, name=password_async_method.name
        )
        assert password_method_model is not None
        assert password_method_model.user_id == user.id


@pytest.mark.anyio
class TestAsyncSignin:
    async def test_missing_identifier_fields(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            await async_auth_manager.signin(
                password_async_method, {"password": "richard"}, name="Aliénor"
            )

    async def test_non_existing_user(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        user = await async_auth_manager.signin(
            password_async_method,
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert user is None

    async def test_invalid_authentication(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        async_storage: MockAsyncStorage[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        user = await async_storage.create(email="alienor@aquitaine.duchy")
        await password_async_method.enroll(user.id, {"password": "richard"})

        authenticated_user = await async_auth_manager.signin(
            password_async_method,
            {"password": "wrongpassword"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is None

    async def test_valid_authentication(
        self,
        async_auth_manager: AsyncAuthManager[UserModel],
        async_storage: MockAsyncStorage[UserModel],
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
    ) -> None:
        user = await async_storage.create(email="alienor@aquitaine.duchy")
        await password_async_method.enroll(user.id, {"password": "richard"})

        authenticated_user = await async_auth_manager.signin(
            password_async_method,
            {"password": "richard"},
            email="alienor@aquitaine.duchy",
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
