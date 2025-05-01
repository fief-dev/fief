import typing


class UserProtocol(typing.Protocol):
    id: typing.Any

    @classmethod
    def identifier_fields(cls) -> tuple[str, ...]:
        """
        Return the identifier fields of the user model.

        Its value is used to uniquely identify the user in the system.
        """
        ...


U = typing.TypeVar("U", bound=UserProtocol)

__all__ = [
    "UserProtocol",
    "U",
]
