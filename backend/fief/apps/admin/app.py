from fastapi import APIRouter, FastAPI

from fief.apps.admin.routers.accounts import router as accounts_router
from fief.apps.admin.routers.auth import router as auth_router
from fief.apps.admin.routers.encryption_keys import router as encryption_keys_router


def include_routers(router: APIRouter) -> APIRouter:
    router.include_router(encryption_keys_router, prefix="/encryption-keys")

    return router


default_tenant_router = include_routers(APIRouter())
tenant_router = include_routers(APIRouter(prefix="/{tenant_slug}"))


app = FastAPI()
app.include_router(accounts_router, prefix="/accounts")
app.include_router(auth_router, prefix="/auth")
app.include_router(default_tenant_router)
app.include_router(tenant_router)

__all__ = ["app"]
