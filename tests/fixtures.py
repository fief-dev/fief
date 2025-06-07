import dataclasses
import typing
import uuid
from collections.abc import Callable

from fief._auth import UserProtocol
from fief.methods._model import MethodModelRawProtocol
from fief.storage import (
    AsyncStorageProtocol,
    AsyncStorageProvider,
    M,
    StorageProtocol,
    StorageProvider,
)


class MockStorage(StorageProtocol[M]):
    def __init__(self, model: type[M]) -> None:
        self.model = model
        self.storage: list[M] = []

    def get_one(self, **kwargs: typing.Any) -> M | None:
        for item in self.storage:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                return item
        return None

    def create(self, **data: typing.Any) -> M:
        instance = self.model(**data)
        self.storage.append(instance)
        return instance

    def update(self, id: typing.Any, **data: typing.Any) -> M | None:
        for item in self.storage:
            if getattr(item, "id", None) == id:
                for key, value in data.items():
                    setattr(item, key, value)
                return item
        return None

    def delete(self, id: typing.Any) -> M | None:
        for item in self.storage:
            if getattr(item, "id", None) == id:
                self.storage.remove(item)
                return item
        return None


class MockAsyncStorage(AsyncStorageProtocol[M]):
    def __init__(self, model: type[M]) -> None:
        self.model = model
        self.storage: list[M] = []

    async def get_one(self, **kwargs: typing.Any) -> M | None:
        for item in self.storage:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                return item
        return None

    async def create(self, **data: typing.Any) -> M:
        instance = self.model(**data)
        self.storage.append(instance)
        return instance

    async def update(self, id: typing.Any, **data: typing.Any) -> M | None:
        for item in self.storage:
            if getattr(item, "id", None) == id:
                for key, value in data.items():
                    setattr(item, key, value)
                return item
        return None

    async def delete(self, id: typing.Any) -> M | None:
        for item in self.storage:
            if getattr(item, "id", None) == id:
                self.storage.remove(item)
                return item
        return None


class MockProvider(StorageProvider):
    storage_class = MockStorage

    def get_model_provider(self, model: type[M]) -> Callable[..., "StorageProtocol[M]"]:
        def _provide() -> StorageProtocol[model]:  # type: ignore[valid-type]
            return self.storage_class(model)

        return _provide


class MockAsyncProvider(AsyncStorageProvider):
    storage_class = MockAsyncStorage

    def get_model_provider(
        self, model: type[M]
    ) -> Callable[..., "AsyncStorageProtocol[M]"]:
        def _provide() -> AsyncStorageProtocol[model]:  # type: ignore[valid-type]
            return self.storage_class(model)

        return _provide


@dataclasses.dataclass
class UserModel(UserProtocol):
    email: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)

    @classmethod
    def identifier_fields(cls) -> tuple[str]:
        return ("email",)


@dataclasses.dataclass
class MethodModel(MethodModelRawProtocol[typing.Any]):
    name: str
    user_id: uuid.UUID
    data: typing.Any
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
