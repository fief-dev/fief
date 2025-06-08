import typing

from starlette.middleware import Middleware
from starlette.requests import Request

from .. import FiefAsync, FiefAsyncRequest
from .._core import U
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
            "Hint: make sure you added the Fief middleware to your application."
        )


class FiefStarlette(typing.Generic[U]):
    def __init__(self, fief: FiefAsync[U]) -> None:
        self.fief = fief

    def get_middleware(self) -> Middleware:
        return Middleware(FiefMiddleware[U], fief=self.fief)

    def get(self, request: Request) -> FiefAsyncRequest[U]:
        try:
            return request.state.fief
        except AttributeError as e:
            raise MissingFiefRequestException() from e


__all__ = ["FiefMiddleware", "FiefStarlette", "MissingFiefRequestException"]
