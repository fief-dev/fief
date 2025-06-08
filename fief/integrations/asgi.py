import typing

if typing.TYPE_CHECKING:
    from asgiref.typing import (
        ASGI3Application,
        ASGIReceiveCallable,
        ASGIReceiveEvent,
        ASGISendCallable,
        Scope,
    )

from .. import FiefAsync
from .._auth import U


class FiefMiddleware(typing.Generic[U]):
    def __init__(self, app: "ASGI3Application", *, fief: FiefAsync[U]) -> None:
        self.app = app
        self.fief = fief

    async def __call__(
        self, scope: "Scope", receive: "ASGIReceiveCallable", send: "ASGISendCallable"
    ) -> None:
        if scope["type"] == "lifespan":

            async def receive_lifespan() -> "ASGIReceiveEvent":
                message = await receive()
                if message["type"] == "lifespan.shutdown":
                    await self.fief.close()
                return message

            await self.app(scope, receive_lifespan, send)
            return

        if scope["type"] in ("http", "websocket"):
            async with self.fief as fief_request:
                state = scope.get("state", {})
                state["fief"] = fief_request
                scope["state"] = state
                await self.app(scope, receive, send)
            return

        return await self.app(scope, receive, send)
