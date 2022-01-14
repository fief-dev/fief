from fastapi import FastAPI

from fief.apps.account.routers.auth import router as auth_router
from fief.apps.account.routers.register import router as register_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(register_router, prefix="/auth")

__all__ = ["app"]
