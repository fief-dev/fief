from fastapi import FastAPI

from fief.apps.supervisor.routers.accounts import router as accounts_router

app = FastAPI()

app.include_router(accounts_router, prefix="/accounts")

__all__ = ["app"]
