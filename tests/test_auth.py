import dataclasses
import uuid

import pytest

from fief._auth import (
    AuthManager,
    MissingIdentifierFieldsException,
    UserAlreadyExistsException,
)
from fief.methods.password import PasswordMethod, PasswordMethodModelData
from tests.fixtures import MockStorage, UserModel


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
