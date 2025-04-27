import typing

M = typing.TypeVar("M")


class StorageProtocol(typing.Protocol):
    """Protocol for storage classes."""

    def get_one(self, model: type[M], **kwargs: typing.Any) -> M | None:
        """Get one object by kwargs.

        Args:
            model: The model class.
            **kwargs: The kwargs to filter by.

        Returns:
            The found object or None if not found.
        """
        ...

    def get_all(
        self, model: type[M], **kwargs: typing.Any
    ) -> typing.Generator[M, None, None]:
        """Get all objects by kwargs.

        Args:
            model: The model class.
            **kwargs: The kwargs to filter by.

        Returns:
            Generator yielding all matching objects.
        """
        ...

    def create(self, model: type[M], **data: typing.Any) -> M:
        """Create a new object.

        Args:
            model: The model class.
            **data: The data to create the object with.

        Returns:
            The newly created object.
        """
        ...

    def update(self, model: type[M], id: typing.Any, **data: typing.Any) -> M | None:
        """Update an existing object.

        Args:
            model: The model class.
            id: The ID of the object to update.
            **data: The data to update the object with.

        Returns:
            The updated object or None if not found.
        """
        ...


class AsyncStorageProtocol(typing.Protocol):
    """Protocol for async storage classes."""

    async def get_one(self, model: type[M], **kwargs: typing.Any) -> M | None:
        """Get one object by kwargs.

        Args:
            model: The model class.
            **kwargs: The kwargs to filter by.

        Returns:
            The found object or None if not found.
        """
        ...

    async def get_all(
        self, model: type[M], **kwargs: typing.Any
    ) -> typing.AsyncGenerator[M, None]:
        """Get all objects by kwargs.

        Args:
            model: The model class.
            **kwargs: The kwargs to filter by.

        Returns:
            AsyncGenerator yielding all matching objects.
        """
        ...

    async def create(self, model: type[M], **data: typing.Any) -> M:
        """Create a new object.

        Args:
            model: The model class.
            **data: The data to create the object with.

        Returns:
            The newly created object.
        """
        ...

    async def update(
        self, model: type[M], id: typing.Any, **data: typing.Any
    ) -> M | None:
        """Update an existing object.

        Args:
            model: The model class.
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
