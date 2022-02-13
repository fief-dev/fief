from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fief.apps.auth.routers.auth import router as auth_router
from fief.apps.auth.routers.register import router as register_router
from fief.apps.auth.routers.reset import router as reset_router
from fief.apps.auth.routers.token import router as token_router
from fief.apps.auth.routers.user import router as user_router
from fief.apps.auth.routers.well_known import router as well_known_router
from fief.apps.auth.templates import templates
from fief.csrf import CSRFCookieSetterMiddleware
from fief.errors import (
    AuthorizeException,
    AuthorizeRedirectException,
    ConsentException,
    FormValidationError,
    LoginException,
    RegisterException,
    ResetPasswordException,
    TokenRequestException,
)
from fief.paths import STATIC_DIRECTORY
from fief.services.authentication_flow import AuthenticationFlow


def include_routers(router: APIRouter) -> APIRouter:
    router.include_router(auth_router)
    router.include_router(register_router)
    router.include_router(reset_router)
    router.include_router(token_router)
    router.include_router(user_router)
    router.include_router(well_known_router, prefix="/.well-known")

    return router


default_tenant_router = include_routers(APIRouter())
tenant_router = include_routers(APIRouter(prefix="/{tenant_slug}"))


app = FastAPI()
app.add_middleware(CSRFCookieSetterMiddleware)
app.include_router(default_tenant_router)
app.include_router(tenant_router)
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")


@app.exception_handler(FormValidationError)
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


@app.exception_handler(RegisterException)
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


@app.exception_handler(AuthorizeException)
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


@app.exception_handler(AuthorizeRedirectException)
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


@app.exception_handler(LoginException)
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


@app.exception_handler(ConsentException)
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


@app.exception_handler(TokenRequestException)
async def token_request_exception_handler(request: Request, exc: TokenRequestException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.error.dict(exclude_none=True),
    )


@app.exception_handler(ResetPasswordException)
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


__all__ = ["app"]
