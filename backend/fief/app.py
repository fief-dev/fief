from fastapi import FastAPI

from fief.routers.register import router as register_router

app = FastAPI()

app.include_router(register_router, prefix="/auth")
