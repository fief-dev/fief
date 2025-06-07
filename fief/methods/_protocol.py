import typing
from collections.abc import Callable, Mapping

from ._model import MM

EnrollKwargs = typing.TypeVar("EnrollKwargs")
AuthenticateKwargs = typing.TypeVar("AuthenticateKwargs")


class MethodProtocol(typing.Protocol[EnrollKwargs, AuthenticateKwargs]):
    """Base protocol for authentication methods."""

    name: str

    def enroll(
        self,
        user_id: typing.Any,
        data: EnrollKwargs,
    ) -> typing.Any: ...  # pragma: no cover

    def authenticate(
        self, user_id: typing.Any | None, data: AuthenticateKwargs
    ) -> bool: ...  # pragma: no cover

    def validate_enroll_request(
        self, data: Mapping[str, typing.Any]
    ) -> EnrollKwargs: ...  # pragma: no cover

    def validate_authenticate_request(
        self, data: Mapping[str, typing.Any]
    ) -> AuthenticateKwargs: ...  # pragma: no cover


MP = typing.TypeVar("MP", bound=MethodProtocol[typing.Any, typing.Any])


class MethodProvider(typing.Generic[MM]):
    method_class: typing.ClassVar[type[MethodProtocol[typing.Any, typing.Any]]]
    model: type[MM]
    name: str

    def __init__(self, model: type[MM], name: str) -> None:
        super().__init__()
        self.model = model
        self.name = name
        self.method_type = self.method_class[model]  # type: ignore[index]

    def get_provider(
        self, storage_component: str
    ) -> Callable[..., MethodProtocol[typing.Any, typing.Any]]:
        raise NotImplementedError()
