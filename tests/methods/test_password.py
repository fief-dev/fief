import dataclasses
import uuid

import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from fief.methods import InvalidMethodRequestException
from fief.methods.password import (
    AlreadyEnrolledException,
    PasswordAsyncMethod,
    PasswordMethod,
    PasswordMethodModelData,
)
from tests.fixtures import MockAsyncStorage, MockStorage


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


@pytest.fixture
def async_storage() -> MockAsyncStorage[PasswordMethodModel]:
    return MockAsyncStorage(PasswordMethodModel)


@pytest.fixture
def password_async_method(
    async_storage: MockAsyncStorage[PasswordMethodModel],
) -> PasswordAsyncMethod[PasswordMethodModel]:
    return PasswordAsyncMethod(
        async_storage, hasher=PasswordHash((Argon2Hasher(), BcryptHasher()))
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


@pytest.mark.anyio
class TestAsyncEnroll:
    async def test_already_enrolled(
        self,
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
        async_storage: MockAsyncStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"

        await async_storage.create(
            name="password",
            user_id=user_id,
            data={"hashed_password": "hashed_password"},
        )

        with pytest.raises(AlreadyEnrolledException):
            await password_async_method.enroll(user_id, {"password": "password"})

    async def test_valid(
        self,
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
        async_storage: MockAsyncStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"

        model = await password_async_method.enroll(user_id, {"password": "password"})

        assert model.id is not None
        assert model.name == "password"
        assert model.user_id == user_id
        assert model.data["hashed_password"] is not None

        stored_model = await async_storage.get_one(id=model.id)
        assert stored_model is not None
        assert stored_model.id == model.id
        assert stored_model.name == "password"
        assert stored_model.user_id == user_id
        assert stored_model.data["hashed_password"] is not None


@pytest.mark.anyio
class TestAsyncAuthenticate:
    async def test_missing_user(
        self, password_async_method: PasswordAsyncMethod[PasswordMethodModel]
    ) -> None:
        result = await password_async_method.authenticate(
            None, {"password": "password"}
        )

        assert result is False

    async def test_not_enrolled(
        self, password_async_method: PasswordAsyncMethod[PasswordMethodModel]
    ) -> None:
        result = await password_async_method.authenticate(
            "user_id", {"password": "password"}
        )

        assert result is False

    async def test_invalid_password(
        self,
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
        async_storage: MockAsyncStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"
        plain_password = "password"

        await async_storage.create(
            name="password",
            user_id=user_id,
            data={
                "hashed_password": password_async_method._hasher.hash(plain_password)
            },
        )

        result = await password_async_method.authenticate(
            user_id, {"password": "invalid"}
        )

        assert result is False

    async def test_invalid_hash(
        self,
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
        async_storage: MockAsyncStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"

        await async_storage.create(
            name="password", user_id=user_id, data={"hashed_password": "invalid_hash"}
        )

        result = await password_async_method.authenticate(
            user_id, {"password": "password"}
        )

        assert result is False

    async def test_valid(
        self,
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
        async_storage: MockAsyncStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"
        plain_password = "password"

        await async_storage.create(
            name="password",
            user_id=user_id,
            data={
                "hashed_password": password_async_method._hasher.hash(plain_password)
            },
        )

        result = await password_async_method.authenticate(
            user_id, {"password": plain_password}
        )

        assert result is True

    async def test_valid_update_hash(
        self,
        password_async_method: PasswordAsyncMethod[PasswordMethodModel],
        async_storage: MockAsyncStorage[PasswordMethodModel],
    ) -> None:
        user_id = "user_id"
        plain_password = "password"
        outdated_hash = BcryptHasher().hash(plain_password)

        stored_model = await async_storage.create(
            name="password", user_id=user_id, data={"hashed_password": outdated_hash}
        )

        result = await password_async_method.authenticate(
            user_id, {"password": plain_password}
        )

        assert result is True

        updated_stored_model = await async_storage.get_one(id=stored_model.id)
        assert updated_stored_model is not None
        assert updated_stored_model.data["hashed_password"] != outdated_hash


class TestValidateEnrollRequest:
    def test_missing_password(
        self, password_method: PasswordMethod[PasswordMethodModel]
    ) -> None:
        with pytest.raises(InvalidMethodRequestException) as excinfo:
            password_method.validate_enroll_request({})

        assert excinfo.value.errors[0]["type"] == "missing"
        assert excinfo.value.errors[0]["loc"] == ("password",)

    def test_valid(self, password_method: PasswordMethod[PasswordMethodModel]) -> None:
        result = password_method.validate_enroll_request({"password": "password"})

        assert result == {"password": "password"}


class TestValidateAuthenticateRequest:
    def test_missing_password(
        self, password_method: PasswordMethod[PasswordMethodModel]
    ) -> None:
        with pytest.raises(InvalidMethodRequestException) as excinfo:
            password_method.validate_authenticate_request({})

        assert excinfo.value.errors[0]["type"] == "missing"
        assert excinfo.value.errors[0]["loc"] == ("password",)

    def test_valid(self, password_method: PasswordMethod[PasswordMethodModel]) -> None:
        result = password_method.validate_authenticate_request({"password": "password"})

        assert result == {"password": "password"}


class TestAsyncValidateEnrollRequest:
    def test_missing_password(
        self, password_async_method: PasswordAsyncMethod[PasswordMethodModel]
    ) -> None:
        with pytest.raises(InvalidMethodRequestException) as excinfo:
            password_async_method.validate_enroll_request({})

        assert excinfo.value.errors[0]["type"] == "missing"
        assert excinfo.value.errors[0]["loc"] == ("password",)

    def test_valid(
        self, password_async_method: PasswordAsyncMethod[PasswordMethodModel]
    ) -> None:
        result = password_async_method.validate_enroll_request({"password": "password"})

        assert result == {"password": "password"}


class TestAsyncValidateAuthenticateRequest:
    def test_missing_password(
        self, password_async_method: PasswordAsyncMethod[PasswordMethodModel]
    ) -> None:
        with pytest.raises(InvalidMethodRequestException) as excinfo:
            password_async_method.validate_authenticate_request({})

        assert excinfo.value.errors[0]["type"] == "missing"
        assert excinfo.value.errors[0]["loc"] == ("password",)

    def test_valid(
        self, password_async_method: PasswordAsyncMethod[PasswordMethodModel]
    ) -> None:
        result = password_async_method.validate_authenticate_request(
            {"password": "password"}
        )

        assert result == {"password": "password"}
