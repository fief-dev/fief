from fastapi import FastAPI

from fief.apps.admin.routers.accounts import router as accounts_router
from fief.apps.admin.routers.encryption_keys import router as encryption_keys_router

app = FastAPI()

app.include_router(accounts_router, prefix="/accounts")
app.include_router(encryption_keys_router, prefix="/encryption-keys")

__all__ = ["app"]
