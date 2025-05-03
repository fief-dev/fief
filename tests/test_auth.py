import dataclasses
import uuid

import pytest

from fief.auth import (
    AuthManager,
    MissingIdentifierFieldsException,
    UnknownMethodException,
    UserAlreadyExistsException,
)
from fief.methods.password import PasswordMethod, PasswordMethodModelData
from tests.fixtures import MockStorage, User


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
def storage() -> MockStorage[User]:
    return MockStorage(User)


@pytest.fixture
def auth_manager(
    storage: MockStorage[User], password_method: PasswordMethod[PasswordMethodModel]
) -> AuthManager[User]:
    return AuthManager(User, storage, methods=[password_method])


class TestSignup:
    def test_unknown_method(self, auth_manager: AuthManager[User]) -> None:
        with pytest.raises(UnknownMethodException):
            auth_manager.signup(("unknown_method", {}), name="Aliénor")

    def test_missing_identifier_fields(self, auth_manager: AuthManager[User]) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            auth_manager.signup(("password", {"password": "richard"}), name="Aliénor")

    def test_user_already_exists(
        self, auth_manager: AuthManager[User], storage: MockStorage[User]
    ) -> None:
        storage.create(email="alienor@aquitaine.duchy")

        with pytest.raises(UserAlreadyExistsException):
            auth_manager.signup(
                ("password", {"password": "richard"}), email="alienor@aquitaine.duchy"
            )

    def test_valid(
        self,
        auth_manager: AuthManager[User],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = auth_manager.signup(
            ("password", {"password": "richard"}), email="alienor@aquitaine.duchy"
        )
        assert user.id is not None
        assert user.email == "alienor@aquitaine.duchy"

        password_method_model = password_method._storage.get_one(
            user_id=user.id, name=password_method.name
        )
        assert password_method_model is not None
        assert password_method_model.user_id == user.id


class TestSignin:
    def test_unknown_method(self, auth_manager: AuthManager[User]) -> None:
        with pytest.raises(UnknownMethodException):
            auth_manager.signin(("unknown_method", {}), name="Aliénor")

    def test_missing_identifier_fields(self, auth_manager: AuthManager[User]) -> None:
        with pytest.raises(MissingIdentifierFieldsException):
            auth_manager.signin(("password", {"password": "richard"}), name="Aliénor")

    def test_non_existing_user(self, auth_manager: AuthManager[User]) -> None:
        user = auth_manager.signin(
            ("password", {"password": "richard"}), email="alienor@aquitaine.duchy"
        )
        assert user is None

    def test_invalid_authentication(
        self,
        auth_manager: AuthManager[User],
        storage: MockStorage[User],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = storage.create(email="alienor@aquitaine.duchy")
        password_method.enroll(user.id, "richard")

        authenticated_user = auth_manager.signin(
            ("password", {"password": "wrongpassword"}), email="alienor@aquitaine.duchy"
        )
        assert authenticated_user is None

    def test_valid_authentication(
        self,
        auth_manager: AuthManager[User],
        storage: MockStorage[User],
        password_method: PasswordMethod[PasswordMethodModel],
    ) -> None:
        user = storage.create(email="alienor@aquitaine.duchy")
        password_method.enroll(user.id, "richard")

        authenticated_user = auth_manager.signin(
            ("password", {"password": "richard"}), email="alienor@aquitaine.duchy"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
