from fastapi import FastAPI

from fief.apps.auth.routers.auth import router as auth_router
from fief.apps.auth.routers.register import router as register_router
from fief.apps.auth.routers.user import router as user_router
from fief.apps.auth.routers.well_known import router as well_known_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(register_router)
app.include_router(user_router)
app.include_router(well_known_router, prefix="/.well-known")

__all__ = ["app"]
