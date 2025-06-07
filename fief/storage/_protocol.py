import typing
from collections.abc import Callable, Sequence

import dishka

M = typing.TypeVar("M")


class StorageProvider(dishka.Provider):
    models: list[type]

    def __init__(self, models: Sequence[type] | None = None):
        super().__init__()
        self.models = list(models or [])
        for model in self.models:
            self.provide(self.get_model_provider(model), scope=dishka.Scope.REQUEST)

    def get_model_provider(self, model: type[M]) -> Callable[..., "StorageProtocol[M]"]:
        raise NotImplementedError()


class StorageProtocol(typing.Protocol[M]):
    """Protocol for storage classes."""

    model: type[M]

    def get_one(self, **kwargs: typing.Any) -> M | None:  # pragma: no cover
        """Get one object by kwargs.

        Args:
            **kwargs: The kwargs to filter by.

        Returns:
            The found object or None if not found.
        """
        ...

    def create(self, **data: typing.Any) -> M:  # pragma: no cover
        """Create a new object.

        Args:
            **data: The data to create the object with.

        Returns:
            The newly created object.
        """
        ...

    def update(
        self, id: typing.Any, **data: typing.Any
    ) -> M | None:  # pragma: no cover
        """Update an existing object.

        Args:
            id: The ID of the object to update.
            **data: The data to update the object with.

        Returns:
            The updated object or None if not found.
        """
        ...

    def delete(self, id: typing.Any) -> M | None:  # pragma: no cover
        """Delete an existing object.

        Args:
            id: The ID of the object to delete.

        Returns:
            The deleted object or None if not found.
        """
        ...


class AsyncStorageProtocol(typing.Protocol[M]):
    """Protocol for async storage classes."""

    model: type[M]

    async def get_one(self, **kwargs: typing.Any) -> M | None:  # pragma: no cover
        """Get one object by kwargs.

        Args:
            **kwargs: The kwargs to filter by.

        Returns:
            The found object or None if not found.
        """
        ...

    async def create(self, **data: typing.Any) -> M:  # pragma: no cover
        """Create a new object.

        Args:
            **data: The data to create the object with.

        Returns:
            The newly created object.
        """
        ...

    async def update(
        self, id: typing.Any, **data: typing.Any
    ) -> M | None:  # pragma: no cover
        """Update an existing object.

        Args:
            id: The ID of the object to update.
            **data: The data to update the object with.

        Returns:
            The updated object or None if not found.
        """
        ...

    async def delete(self, id: typing.Any) -> M | None:  # pragma: no cover
        """Delete an existing object.

        Args:
            id: The ID of the object to delete.

        Returns:
            The deleted object or None if not found.
        """
        ...


__all__ = [
    "M",
    "StorageProtocol",
    "AsyncStorageProtocol",
    "StorageProvider",
]
