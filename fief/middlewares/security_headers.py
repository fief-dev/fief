import functools

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        send = functools.partial(self.send, send=send, scope=scope)
        await self.app(scope, receive, send)

    async def send(self, message: Message, send: Send, scope: Scope) -> None:
        if message["type"] != "http.response.start":
            await send(message)
            return

        message.setdefault("headers", [])
        headers = MutableHeaders(scope=message)

        headers.append("content-security-policy", "frame-ancestors 'self'")
        headers.append("x-frame-options", "SAMEORIGIN")
        headers.append("referrer-policy", "strict-origin-when-cross-origin")
        headers.append("x-content-type-options", "nosniff")
        headers.append("permissions-policy", "geolocation=() camera=(), microphone=()")

        await send(message)
