from fastapi import FastAPI

from fief.routers.auth import router as auth_router
from fief.routers.register import router as register_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth/token")
app.include_router(register_router, prefix="/auth")
