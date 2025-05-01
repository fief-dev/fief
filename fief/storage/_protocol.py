import typing

M = typing.TypeVar("M")


class StorageProtocol(typing.Protocol[M]):
    """Protocol for storage classes."""

    model: type[M]

    def get_one(self, **kwargs: typing.Any) -> M | None:
        """Get one object by kwargs.

        Args:
            **kwargs: The kwargs to filter by.

        Returns:
            The found object or None if not found.
        """
        ...

    def create(self, **data: typing.Any) -> M:
        """Create a new object.

        Args:
            **data: The data to create the object with.

        Returns:
            The newly created object.
        """
        ...

    def update(self, id: typing.Any, **data: typing.Any) -> M | None:
        """Update an existing object.

        Args:
            id: The ID of the object to update.
            **data: The data to update the object with.

        Returns:
            The updated object or None if not found.
        """
        ...


class AsyncStorageProtocol(typing.Protocol[M]):
    """Protocol for async storage classes."""

    model: type[M]

    async def get_one(self, **kwargs: typing.Any) -> M | None:
        """Get one object by kwargs.

        Args:
            **kwargs: The kwargs to filter by.

        Returns:
            The found object or None if not found.
        """
        ...

    async def create(self, **data: typing.Any) -> M:
        """Create a new object.

        Args:
            **data: The data to create the object with.

        Returns:
            The newly created object.
        """
        ...

    async def update(self, id: typing.Any, **data: typing.Any) -> M | None:
        """Update an existing object.

        Args:
            id: The ID of the object to update.
            **data: The data to update the object with.

        Returns:
            The updated object or None if not found.
        """
        ...


__all__ = [
    "M",
    "StorageProtocol",
    "AsyncStorageProtocol",
]
