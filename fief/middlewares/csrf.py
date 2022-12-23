import functools
import http.cookies

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from fief.settings import settings

CSRF_ATTRIBUTE_NAME = "csrftoken"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFCookieSetterMiddleware:
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

        if csrftoken := scope.get(CSRF_ATTRIBUTE_NAME):
            message.setdefault("headers", [])
            headers = MutableHeaders(scope=message)

            cookie: http.cookies.BaseCookie = http.cookies.SimpleCookie()
            cookie_name = settings.csrf_cookie_name
            cookie[cookie_name] = csrftoken
            cookie[cookie_name]["secure"] = settings.csrf_cookie_secure
            cookie[cookie_name]["httponly"] = True
            headers.append("set-cookie", cookie.output(header="").strip())

        await send(message)
