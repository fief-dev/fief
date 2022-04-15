from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from fief.apps.auth.exception_handlers import exception_handlers
from fief.apps.auth.routers.auth import router as auth_router
from fief.apps.auth.routers.register import router as register_router
from fief.apps.auth.routers.reset import router as reset_router
from fief.apps.auth.routers.token import router as token_router
from fief.apps.auth.routers.user import router as user_router
from fief.apps.auth.routers.well_known import router as well_known_router
from fief.cors import CORSMiddlewarePath
from fief.csrf import CSRFCookieSetterMiddleware
from fief.paths import STATIC_DIRECTORY


def include_routers(router: APIRouter) -> APIRouter:
    router.include_router(auth_router, include_in_schema=False)
    router.include_router(register_router, include_in_schema=False)
    router.include_router(reset_router, include_in_schema=False)
    router.include_router(token_router, prefix="/api")
    router.include_router(user_router, prefix="/api")
    router.include_router(well_known_router, prefix="/.well-known")

    return router


default_tenant_router = include_routers(APIRouter())
tenant_router = include_routers(APIRouter(prefix="/{tenant_slug}"))


app = FastAPI(title="Fief Authentication API")
app.add_middleware(CSRFCookieSetterMiddleware)
app.add_middleware(
    CORSMiddlewarePath,
    path_regex=r"^/api|^/\.well-known",
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "X-Requested-With"],
)
app.include_router(default_tenant_router)
app.include_router(tenant_router)
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="auth:static")

for (exc, handler) in exception_handlers.items():
    app.add_exception_handler(exc, handler)


__all__ = ["app"]
