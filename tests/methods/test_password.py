import dataclasses
import uuid

import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from fief.methods.password import (
    AlreadyEnrolledException,
    PasswordMethod,
    PasswordMethodModelData,
)
from tests.fixtures import MockStorage


@dataclasses.dataclass
class PasswordMethodModel:
    name: str
    user_id: str
    data: PasswordMethodModelData
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@pytest.fixture
def storage() -> MockStorage[PasswordMethodModel]:
    return MockStorage(PasswordMethodModel)


@pytest.fixture
def password_method(
    storage: MockStorage[PasswordMethodModel],
) -> PasswordMethod[PasswordMethodModel]:
    return PasswordMethod(
        storage, hasher=PasswordHash((Argon2Hasher(), BcryptHasher()))
    )


class TestEnroll:
    def test_already_enrolled(
        self,
        password_method: PasswordMethod[PasswordMethodModel],
        storage: MockStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"

        storage.create(
            name="password",
            user_id=user_id,
            data={"hashed_password": "hashed_password"},
        )

        with pytest.raises(AlreadyEnrolledException):
            password_method.enroll(user_id, {"password": "password"})

    def test_valid(
        self,
        password_method: PasswordMethod[PasswordMethodModel],
        storage: MockStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"

        model = password_method.enroll(user_id, {"password": "password"})

        assert model.id is not None
        assert model.name == "password"
        assert model.user_id == user_id
        assert model.data["hashed_password"] is not None

        stored_model = storage.get_one(id=model.id)
        assert stored_model is not None
        assert stored_model.id == model.id
        assert stored_model.name == "password"
        assert stored_model.user_id == user_id
        assert stored_model.data["hashed_password"] is not None


class TestAuthenticate:
    def test_missing_user(
        self, password_method: PasswordMethod[PasswordMethodModel]
    ) -> None:
        result = password_method.authenticate(None, {"password": "password"})

        assert result is False

    def test_not_enrolled(
        self, password_method: PasswordMethod[PasswordMethodModel]
    ) -> None:
        result = password_method.authenticate("user_id", {"password": "password"})

        assert result is False

    def test_invalid_password(
        self,
        password_method: PasswordMethod[PasswordMethodModel],
        storage: MockStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"
        plain_password = "password"

        storage.create(
            name="password",
            user_id=user_id,
            data={"hashed_password": password_method._hasher.hash(plain_password)},
        )

        result = password_method.authenticate(user_id, {"password": "invalid"})

        assert result is False

    def test_invalid_hash(
        self,
        password_method: PasswordMethod[PasswordMethodModel],
        storage: MockStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"

        storage.create(
            name="password", user_id=user_id, data={"hashed_password": "invalid_hash"}
        )

        result = password_method.authenticate(user_id, {"password": "password"})

        assert result is False

    def test_valid(
        self,
        password_method: PasswordMethod[PasswordMethodModel],
        storage: MockStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"
        plain_password = "password"

        storage.create(
            name="password",
            user_id=user_id,
            data={"hashed_password": password_method._hasher.hash(plain_password)},
        )

        result = password_method.authenticate(user_id, {"password": plain_password})

        assert result is True

    def test_valid_update_hash(
        self,
        password_method: PasswordMethod[PasswordMethodModel],
        storage: MockStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"
        plain_password = "password"
        outdated_hash = BcryptHasher().hash(plain_password)

        stored_model = storage.create(
            name="password", user_id=user_id, data={"hashed_password": outdated_hash}
        )

        result = password_method.authenticate(user_id, {"password": plain_password})

        assert result is True

        updated_stored_model = storage.get_one(id=stored_model.id)
        assert updated_stored_model is not None
        assert updated_stored_model.data["hashed_password"] != outdated_hash
