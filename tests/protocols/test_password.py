import dataclasses
import typing
import uuid

import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from fief.protocols.password import (
    AlreadyEnrolledException,
    Password,
    PasswordModelData,
)
from tests.fixtures import MockStorage


@dataclasses.dataclass
class PasswordModel:
    type: typing.Literal["password"]
    user_id: str
    data: PasswordModelData
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)


@pytest.fixture
def storage() -> MockStorage[PasswordModel]:
    return MockStorage(PasswordModel)


@pytest.fixture
def password(storage: MockStorage[PasswordModel]) -> Password[PasswordModel]:
    return Password(storage, hasher=PasswordHash((Argon2Hasher(), BcryptHasher())))


class TestEnroll:
    def test_already_enrolled(
        self, password: Password[PasswordModel], storage: MockStorage[PasswordModel]
    ) -> None:
        user_id = "user_id"

        storage.create(
            type="password",
            user_id=user_id,
            data={"hashed_password": "hashed_password"},
        )

        with pytest.raises(AlreadyEnrolledException):
            password.enroll(user_id, "password")

    def test_valid(
        self, password: Password[PasswordModel], storage: MockStorage[PasswordModel]
    ) -> None:
        user_id = "user_id"

        model = password.enroll(user_id, "password")

        assert model.id is not None
        assert model.type == "password"
        assert model.user_id == user_id
        assert model.data["hashed_password"] is not None

        stored_model = storage.get_one(id=model.id)
        assert stored_model is not None
        assert stored_model.id == model.id
        assert stored_model.type == "password"
        assert stored_model.user_id == user_id
        assert stored_model.data["hashed_password"] is not None


class TestAuthenticate:
    def test_missing_user(self, password: Password[PasswordModel]) -> None:
        result = password.authenticate(None, "password")

        assert result is False

    def test_not_enrolled(self, password: Password[PasswordModel]) -> None:
        result = password.authenticate("user_id", "password")

        assert result is False

    def test_invalid_password(
        self, password: Password[PasswordModel], storage: MockStorage[PasswordModel]
    ) -> None:
        user_id = "user_id"
        plain_password = "password"

        storage.create(
            type="password",
            user_id=user_id,
            data={"hashed_password": password._hasher.hash(plain_password)},
        )

        result = password.authenticate(user_id, "invalid")

        assert result is False

    def test_invalid_hash(
        self, password: Password[PasswordModel], storage: MockStorage[PasswordModel]
    ) -> None:
        user_id = "user_id"

        storage.create(
            type="password", user_id=user_id, data={"hashed_password": "invalid_hash"}
        )

        result = password.authenticate(user_id, "password")

        assert result is False

    def test_valid(
        self, password: Password[PasswordModel], storage: MockStorage[PasswordModel]
    ) -> None:
        user_id = "user_id"
        plain_password = "password"

        storage.create(
            type="password",
            user_id=user_id,
            data={"hashed_password": password._hasher.hash(plain_password)},
        )

        result = password.authenticate(user_id, plain_password)

        assert result is True

    def test_valid_update_hash(
        self, password: Password[PasswordModel], storage: MockStorage[PasswordModel]
    ) -> None:
        user_id = "user_id"
        plain_password = "password"
        outdated_hash = BcryptHasher().hash(plain_password)

        stored_model = storage.create(
            type="password", user_id=user_id, data={"hashed_password": outdated_hash}
        )

        result = password.authenticate(user_id, plain_password)

        assert result is True

        updated_stored_model = storage.get_one(id=stored_model.id)
        assert updated_stored_model is not None
        assert updated_stored_model.data["hashed_password"] != outdated_hash
