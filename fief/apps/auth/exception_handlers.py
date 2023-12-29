from collections.abc import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse

from fief.apps.auth.forms.auth import LoginForm
from fief.exceptions import (
    AuthorizeException,
    AuthorizeRedirectException,
    LoginException,
    LogoutException,
    OAuthException,
    TokenRequestException,
)
from fief.forms import FormHelper
from fief.services.authentication_flow import AuthenticationFlow
from fief.templates import templates

exception_handlers: dict[type[Exception], Callable] = {}


async def authorize_exception_handler(request: Request, exc: AuthorizeException):
    return templates.TemplateResponse(
        request,
        "auth/authorize.html",
        {
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


async def login_exception_handler(
    request: Request, exc: LoginException | OAuthException
):
    form_helper = FormHelper(
        LoginForm,
        "auth/login.html",
        request=request,
        context={"tenant": exc.tenant},
    )
    form = await form_helper.get_form()

    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "form": form,
            "error": exc.error.error_description,
            "oauth_providers": exc.oauth_providers,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[LoginException] = login_exception_handler
exception_handlers[OAuthException] = login_exception_handler


async def token_request_exception_handler(request: Request, exc: TokenRequestException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.error.model_dump(exclude_none=True),
    )


exception_handlers[TokenRequestException] = token_request_exception_handler


async def logout_exception_handler(request: Request, exc: LogoutException):
    return templates.TemplateResponse(
        request,
        "auth/logout.html",
        {
            "error": exc.error.error_description,
            "tenant": exc.tenant,
            "fatal_error": True,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[LogoutException] = logout_exception_handler

__all__ = ["exception_handlers"]
