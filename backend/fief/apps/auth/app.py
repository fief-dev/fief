from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fief.apps.auth.routers.auth import router as auth_router
from fief.apps.auth.routers.register import router as register_router
from fief.apps.auth.routers.user import router as user_router
from fief.apps.auth.routers.well_known import router as well_known_router
from fief.apps.auth.templates import templates
from fief.errors import AuthorizeException, LoginException, TokenRequestException


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


@app.exception_handler(LoginException)
async def login_exception_handler(request: Request, exc: LoginException):
    return templates.TemplateResponse(
        "authorize.html",
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
