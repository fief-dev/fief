from typing import Callable, Dict, Type

from fastapi import Request, status
from fastapi.responses import JSONResponse

from fief.apps.auth.templates import templates
from fief.exceptions import (
    AuthorizeException,
    AuthorizeRedirectException,
    ConsentException,
    FormValidationError,
    LoginException,
    RegisterException,
    ResetPasswordException,
    TokenRequestException,
)
from fief.services.authentication_flow import AuthenticationFlow

exception_handlers: Dict[Type[Exception], Callable] = {}


async def form_validation_error_handler(request: Request, exc: FormValidationError):
    return templates.LocaleTemplateResponse(
        exc.template,
        {
            "request": request,
            "form_errors": exc.form_errors(),
            "tenant": exc.tenant,
            "fatal_error": False,
        },
        translations=request.scope["translations"],
        status_code=status.HTTP_400_BAD_REQUEST,
    )


exception_handlers[FormValidationError] = form_validation_error_handler


async def register_exception_handler(request: Request, exc: RegisterException):
    return templates.LocaleTemplateResponse(
        "register.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "form_data": exc.form_data,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        translations=request.scope["translations"],
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[RegisterException] = register_exception_handler


async def authorize_exception_handler(request: Request, exc: AuthorizeException):
    return templates.LocaleTemplateResponse(
        "authorize.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "tenant": exc.tenant,
            "fatal_error": True,
        },
        translations=request.scope["translations"],
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[AuthorizeException] = authorize_exception_handler


async def authorize_redirect_exception_handler(
    request: Request, exc: AuthorizeRedirectException
):
    return AuthenticationFlow.get_authorization_code_error_redirect(
        exc.redirect_uri,
        exc.error.error,
        error_description=exc.error.error_description,
        error_uri=exc.error.error_uri,
        state=exc.state,
    )


exception_handlers[AuthorizeRedirectException] = authorize_redirect_exception_handler


async def login_exception_handler(request: Request, exc: LoginException):
    return templates.LocaleTemplateResponse(
        "login.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        translations=request.scope["translations"],
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[LoginException] = login_exception_handler


async def consent_exception_handler(request: Request, exc: ConsentException):
    return templates.LocaleTemplateResponse(
        "consent.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "client": exc.client,
            "scopes": exc.scope,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        translations=request.scope["translations"],
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[ConsentException] = consent_exception_handler


async def token_request_exception_handler(request: Request, exc: TokenRequestException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.error.dict(exclude_none=True),
    )


exception_handlers[TokenRequestException] = token_request_exception_handler


async def reset_password_exception_handler(
    request: Request, exc: ResetPasswordException
):
    return templates.LocaleTemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "form_data": exc.form_data,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        translations=request.scope["translations"],
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


exception_handlers[ResetPasswordException] = reset_password_exception_handler

__all__ = ["exception_handlers"]
