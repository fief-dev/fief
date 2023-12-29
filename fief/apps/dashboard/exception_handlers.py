from collections.abc import Callable

from fastapi import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from fief.templates import templates

exception_handlers: dict[type[Exception], Callable] = {}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = getattr(exc, "headers", None)
    return templates.TemplateResponse(
        request,
        "admin/error.html",
        {
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
        status_code=exc.status_code,
        headers=headers,
    )


exception_handlers[StarletteHTTPException] = http_exception_handler


__all__ = ["exception_handlers"]
