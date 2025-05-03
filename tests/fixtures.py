import dataclasses
import typing
import uuid

from fief.auth import UserProtocol
from fief.storage import AsyncStorageProtocol, M, StorageProtocol


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


@dataclasses.dataclass
class User(UserProtocol):
    email: str
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)

    @classmethod
    def identifier_fields(cls) -> tuple[str]:
        return ("email",)
