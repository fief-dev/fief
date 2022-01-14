from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fief.apps import account_app, supervisor_app
from fief.settings import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/account", account_app)
app.mount("/supervisor", supervisor_app)

__all__ = ["app"]
