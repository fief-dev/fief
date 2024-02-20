from os import environ

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from redis.exceptions import RedisError
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.redis import RedisIntegration
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from fief import __version__
from fief.apps import api_app, auth_app, dashboard_app
from fief.db import AsyncSession
from fief.dependencies.db import get_main_async_session
from fief.errors import APIErrorCode
from fief.lifespan import lifespan
from fief.middlewares.x_forwarded_host import XForwardedHostMiddleware
from fief.settings import settings
from fief.tasks.base import redis_broker

sentry_sdk.init(
    dsn=settings.sentry_dsn_server,
    environment=settings.environment.value,
    traces_sample_rate=0.1,
    release=__version__,
    integrations=[RedisIntegration()],
)

app = FastAPI(lifespan=lifespan, openapi_url=None)

app.add_middleware(SentryAsgiMiddleware)
app.add_middleware(
    XForwardedHostMiddleware,
    trusted_hosts=environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"),
)


@app.get("/admin")
async def get_admin():
    return RedirectResponse("/admin/", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.get("/healthz")
async def healthz(session: AsyncSession = Depends(get_main_async_session)):
    try:
        await session.execute(select(1))
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.SERVER_DATABASE_NOT_AVAILABLE,
        ) from e

    try:
        redis_broker.client.ping()
    except RedisError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.SERVER_REDIS_NOT_AVAILABLE,
        ) from e

    return {"message": "Everything is ready, my lord 🏰"}


app.mount("/admin/api", api_app)
app.mount("/admin", dashboard_app)
app.mount("/", auth_app)

__all__ = ["app"]
