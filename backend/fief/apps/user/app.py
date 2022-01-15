from fastapi import FastAPI

from fief.apps.user.routers.auth import router as auth_router
from fief.apps.user.routers.register import router as register_router
from fief.apps.user.routers.user import router as user_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(register_router)
app.include_router(user_router)

__all__ = ["app"]
