import json
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic.error_wrappers import ErrorWrapper


async def get_request_json(request: Request) -> dict[str, Any]:
    try:
        return await request.json()
    except json.JSONDecodeError as e:
        # Taken from FastAPI to mimic its builtin logic when encountering invalid JSON
        # Ref: https://github.com/tiangolo/fastapi/blob/7b3727e03e84ca202d450ba3d702d5cd37025d60/fastapi/routing.py#L217-L220
        raise RequestValidationError(
            [ErrorWrapper(e, ("body", e.pos))], body=e.doc
        ) from e
