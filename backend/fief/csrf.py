import secrets
from typing import Optional

from fastapi import Cookie, Form, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from fief.errors import APIErrorCode

CSRF_ATTRIBUTE_NAME = "csrftoken"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


async def check_csrf(
    request: Request,
    challenge_csrf_token: Optional[str] = Cookie(
        None, alias=CSRF_ATTRIBUTE_NAME, include_in_schema=False
    ),
    submitted_csrf_token: Optional[str] = Form(
        None, alias=CSRF_ATTRIBUTE_NAME, include_in_schema=False
    ),
):
    if request.method not in SAFE_METHODS:
        if (
            challenge_csrf_token is None
            or submitted_csrf_token is None
            or not secrets.compare_digest(challenge_csrf_token, submitted_csrf_token)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIErrorCode.CSRF_CHECK_FAILED,
            )

    request.scope[CSRF_ATTRIBUTE_NAME] = secrets.token_urlsafe()


class CSRFCookieSetterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        response = await call_next(request)
        if csrftoken := request.scope.get(CSRF_ATTRIBUTE_NAME):
            response.set_cookie(
                CSRF_ATTRIBUTE_NAME, csrftoken, secure=True, httponly=True
            )
        return response
