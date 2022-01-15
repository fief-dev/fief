from fastapi import FastAPI

from fief.apps.account.routers.auth import router as auth_router
from fief.apps.account.routers.register import router as register_router
from fief.apps.account.routers.well_known import router as well_known_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(register_router, prefix="/auth")
app.include_router(well_known_router, prefix="/.well-known")

__all__ = ["app"]
