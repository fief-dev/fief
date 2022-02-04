import secrets
from typing import Optional

from fastapi import Cookie, Form, HTTPException, Request, status

from fief.errors import APIErrorCode

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


async def check_csrf(
    request: Request,
    challenge_csrf_token: Optional[str] = Cookie(
        None, alias="csrftoken", include_in_schema=False
    ),
    submitted_csrf_token: Optional[str] = Form(
        None, alias="csrftoken", include_in_schema=False
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

    request.scope["csrftoken"] = secrets.token_urlsafe()
