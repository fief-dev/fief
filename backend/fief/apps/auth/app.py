from fastapi import APIRouter, FastAPI

from fief.apps.auth.routers.auth import router as auth_router
from fief.apps.auth.routers.register import router as register_router
from fief.apps.auth.routers.user import router as user_router
from fief.apps.auth.routers.well_known import router as well_known_router
from fief.errors import TokenRequestException, token_request_exception_handler


def include_routers(router: APIRouter) -> APIRouter:
    router.include_router(auth_router)
    router.include_router(register_router)
    router.include_router(user_router)
    router.include_router(well_known_router, prefix="/.well-known")

    return router


default_tenant_router = include_routers(APIRouter())
tenant_router = include_routers(APIRouter(prefix="/{tenant_slug}"))


app = FastAPI()
app.add_exception_handler(TokenRequestException, token_request_exception_handler)
app.include_router(default_tenant_router)
app.include_router(tenant_router)


__all__ = ["app"]
