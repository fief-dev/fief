import typing

from starlette.requests import Request

from .. import FiefAsync, FiefAsyncRequest
from .._auth import U, UserProtocol
from .._exceptions import FiefException

if typing.TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

    class FiefMiddleware(typing.Generic[U]):
        def __init__(self, app: "ASGIApp", *, fief: FiefAsync[U]) -> None: ...

        async def __call__(
            self, scope: "Scope", receive: "Receive", send: "Send"
        ) -> None: ...
else:
    from .asgi import FiefMiddleware


class MissingFiefRequestException(FiefException):
    """Exception raised when the Fief request is missing in the request state."""

    def __init__(self) -> None:
        super().__init__(
            "Fief request is missing in the request state. "
            "Hint: use FiefMiddleware to add it."
        )


def get_fief(request: Request) -> FiefAsyncRequest[UserProtocol]:
    """
    Get the Fief request from the Starlette request state.

    Args:
        request: The Starlette request object.

    Returns:
        The Fief request object.

    Raises:
        MissingFiefRequestException: If the Fief request is not found in the request state.
    """
    try:
        return request.state.fief
    except AttributeError as e:
        raise MissingFiefRequestException() from e


__all__ = ["FiefMiddleware", "get_fief", "MissingFiefRequestException"]
