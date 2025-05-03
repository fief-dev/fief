import typing
from collections.abc import Mapping


class MethodProtocol(typing.Protocol):
    """Base protocol for authentication methods."""

    name: str

    def enroll(
        self, user_id: typing.Any, *args: typing.Any, **kwargs: typing.Any
    ) -> typing.Any: ...

    def authenticate(
        self, user_id: typing.Any | None, *args: typing.Any, **kwargs: typing.Any
    ) -> bool: ...

    def validate_enroll_request(
        self, data: Mapping[str, typing.Any]
    ) -> Mapping[str, typing.Any]: ...

    def validate_authenticate_request(
        self, data: Mapping[str, typing.Any]
    ) -> Mapping[str, typing.Any]: ...
