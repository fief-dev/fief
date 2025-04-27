import typing

from fief.storage import AsyncStorageProtocol, M, StorageProtocol


class MockStorage(StorageProtocol):
    def __init__(self) -> None:
        self.storage: dict[type, list[typing.Any]] = {}

    def get_one(self, model: type[M], **kwargs: typing.Any) -> M | None:
        if model not in self.storage:
            return None
        for item in self.storage[model]:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                return item
        return None

    def get_all(
        self, model: type[M], **kwargs: typing.Any
    ) -> typing.Generator[M, None, None]:
        if model not in self.storage:
            return
        for item in self.storage[model]:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                yield item

    def create(self, model: type[M], **data: typing.Any) -> M:
        if model not in self.storage:
            self.storage[model] = []
        instance = model(**data)
        self.storage[model].append(instance)
        return instance

    def update(self, model: type[M], id: typing.Any, **data: typing.Any) -> M | None:
        if model not in self.storage:
            return None
        for item in self.storage[model]:
            if getattr(item, "id", None) == id:
                for key, value in data.items():
                    setattr(item, key, value)
                return item
        return None


class MockAsyncStorage(AsyncStorageProtocol):
    def __init__(self) -> None:
        self.storage: dict[type, list[typing.Any]] = {}

    async def get_one(self, model: type[M], **kwargs: typing.Any) -> M | None:
        if model not in self.storage:
            return None
        for item in self.storage[model]:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                return item
        return None

    async def get_all(
        self, model: type[M], **kwargs: typing.Any
    ) -> typing.AsyncGenerator[M, None]:
        async def _generator() -> typing.AsyncGenerator[M, None]:
            if model not in self.storage:
                return
            for item in self.storage[model]:
                if all(getattr(item, k) == v for k, v in kwargs.items()):
                    yield item

        return _generator()

    async def create(self, model: type[M], **data: typing.Any) -> M:
        if model not in self.storage:
            self.storage[model] = []
        instance = model(**data)
        self.storage[model].append(instance)
        return instance

    async def update(
        self, model: type[M], id: typing.Any, **data: typing.Any
    ) -> M | None:
        if model not in self.storage:
            return None
        for item in self.storage[model]:
            if getattr(item, "id", None) == id:
                for key, value in data.items():
                    setattr(item, key, value)
                return item
        return None
