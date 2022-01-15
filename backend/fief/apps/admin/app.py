from fastapi import FastAPI

from fief.apps.admin.routers.accounts import router as accounts_router
from fief.apps.admin.routers.encryption_keys import router as encryption_keys_router
from fief.apps.admin.routers.well_known import router as well_known_router

app = FastAPI()

app.include_router(accounts_router, prefix="/accounts")
app.include_router(encryption_keys_router, prefix="/encryption-keys")
app.include_router(well_known_router, prefix="/.well-known")

__all__ = ["app"]
