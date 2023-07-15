import json
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError


async def get_request_json(request: Request) -> dict[str, Any]:
    try:
        return await request.json()
    except json.JSONDecodeError as e:
        # Taken from FastAPI to mimic its builtin logic when encountering invalid JSON
        # Ref: https://github.com/tiangolo/fastapi/blob/f7e3559bd5997f831fb9b02bef9c767a50facbc3/fastapi/routing.py#L244-L256
        raise RequestValidationError(
            [
                {
                    "type": "json_invalid",
                    "loc": ("body", e.pos),
                    "msg": "JSON decode error",
                    "input": {},
                    "ctx": {"error": e.msg},
                }
            ],
            body=e.doc,
        ) from e
