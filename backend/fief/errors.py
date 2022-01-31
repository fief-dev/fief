from enum import Enum

from fastapi import Request, status
from fastapi.responses import JSONResponse

from fief.schemas.auth import TokenErrorResponse


class ErrorCode(str, Enum):
    ACCOUNT_DB_CONNECTION_ERROR = "ACCOUNT_DB_CONNECTION_ERROR"
    AUTH_INVALID_CLIENT_ID = "AUTH_INVALID_CLIENT_ID"


class TokenRequestException(Exception):
    def __init__(self, error: TokenErrorResponse) -> None:
        self.error = error


async def token_request_exception_handler(request: Request, exc: TokenRequestException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.error.dict(exclude_none=True),
    )
