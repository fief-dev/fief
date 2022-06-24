from typing import Callable, Dict, Type

from fastapi import Request, status
from fastapi.responses import JSONResponse

from fief.apps.auth.templates import templates
from fief.exceptions import (
    AuthorizeException,
    AuthorizeRedirectException,
    LoginException,
    LogoutException,
    TokenRequestException,
)
from fief.services.authentication_flow import AuthenticationFlow

exception_handlers: Dict[Type[Exception], Callable] = {}


async def authorize_exception_handler(request: Request, exc: AuthorizeException):
    return templates.TemplateResponse(
        "authorize.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "tenant": exc.tenant,
            "fatal_error": True,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[AuthorizeException] = authorize_exception_handler


async def authorize_redirect_exception_handler(
    request: Request, exc: AuthorizeRedirectException
):
    return AuthenticationFlow.get_authorization_code_error_redirect(
        exc.redirect_uri,
        exc.response_mode,
        exc.error.error,
        error_description=exc.error.error_description,
        error_uri=exc.error.error_uri,
        state=exc.state,
    )


exception_handlers[AuthorizeRedirectException] = authorize_redirect_exception_handler


async def login_exception_handler(request: Request, exc: LoginException):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[LoginException] = login_exception_handler


async def token_request_exception_handler(request: Request, exc: TokenRequestException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.error.dict(exclude_none=True),
    )


exception_handlers[TokenRequestException] = token_request_exception_handler


async def logout_exception_handler(request: Request, exc: LogoutException):
    return templates.TemplateResponse(
        "logout.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "tenant": exc.tenant,
            "fatal_error": True,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[LogoutException] = logout_exception_handler

__all__ = ["exception_handlers"]
