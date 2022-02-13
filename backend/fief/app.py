import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.redis import RedisIntegration

from fief import __version__
from fief.apps import admin_app, auth_app
from fief.db import account_engine_manager
from fief.services.account_creation import create_global_fief_account
from fief.settings import settings

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment.value,
    release=__version__,
    integrations=[RedisIntegration()],
)

app = FastAPI(openapi_url=None)

app.add_middleware(SentryAsgiMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/admin", admin_app)
app.mount("/", auth_app)


@app.on_event("startup")
async def on_startup():
    await create_global_fief_account()


@app.on_event("shutdown")
async def on_shutdown():
    await account_engine_manager.close_all()


__all__ = ["app"]
