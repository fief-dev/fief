import re

from fastapi.middleware.cors import CORSMiddleware
from starlette.types import Receive, Scope, Send


class CORSMiddlewarePath(CORSMiddleware):
    def __init__(self, path_regex: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.path_regex = re.compile(path_regex)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if not self.path_regex.match(path):
            await self.app(scope, receive, send)
            return

        return await super().__call__(scope, receive, send)
