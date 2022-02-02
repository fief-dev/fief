from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fief.apps.auth.routers.auth import router as auth_router
from fief.apps.auth.routers.register import router as register_router
from fief.apps.auth.routers.user import router as user_router
from fief.apps.auth.routers.well_known import router as well_known_router
from fief.apps.auth.templates import templates
from fief.errors import (
    AuthorizeException,
    AuthorizeRedirectException,
    FormValidationError,
    LoginException,
    RegisterException,
    TokenRequestException,
)
from fief.services.authorization_code_flow import AuthorizationCodeFlow


def include_routers(router: APIRouter) -> APIRouter:
    router.include_router(auth_router)
    router.include_router(register_router)
    router.include_router(user_router)
    router.include_router(well_known_router, prefix="/.well-known")

    return router


default_tenant_router = include_routers(APIRouter())
tenant_router = include_routers(APIRouter(prefix="/{tenant_slug}"))


app = FastAPI()
app.include_router(default_tenant_router)
app.include_router(tenant_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(FormValidationError)
async def form_validation_error_handler(request: Request, exc: FormValidationError):
    return templates.TemplateResponse(
        exc.template,
        {
            "request": request,
            "form_errors": exc.form_errors(),
            "tenant": exc.tenant,
            "fatal_error": False,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.exception_handler(RegisterException)
async def register_exception_handler(request: Request, exc: RegisterException):
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "error": exc.error.error_description,
            "form_data": exc.form_data,
            "tenant": exc.tenant,
            "fatal_error": exc.fatal,
        },
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={"X-Fief-Error": exc.error.error},
    )


@app.exception_handler(AuthorizeException)
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


@app.exception_handler(AuthorizeRedirectException)
async def authorize_redirect_exception_handler(
    request: Request, exc: AuthorizeRedirectException
):
    return AuthorizationCodeFlow.get_error_redirect(
        exc.redirect_uri,
        exc.error.error,
        error_description=exc.error.error_description,
        error_uri=exc.error.error_uri,
        state=exc.state,
    )


@app.exception_handler(LoginException)
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


@app.exception_handler(TokenRequestException)
async def token_request_exception_handler(request: Request, exc: TokenRequestException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.error.dict(exclude_none=True),
    )


__all__ = ["app"]
