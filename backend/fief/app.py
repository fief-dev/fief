from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fief.apps import admin_app, user_app
from fief.services.account_creation import create_global_fief_account
from fief.settings import settings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", admin_app)
app.mount("/u", user_app)


@app.on_event("startup")
async def on_startup():
    await create_global_fief_account()


__all__ = ["app"]
