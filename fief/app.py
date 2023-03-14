import functools

import sentry_sdk
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.redis import RedisIntegration

from fief import __version__
from fief.apps import api_app, auth_app, dashboard_app
from fief.db.workspace import get_workspace_session
from fief.dependencies.db import main_async_session_maker, workspace_engine_manager
from fief.logger import init_audit_logger, logger
from fief.settings import settings

sentry_sdk.init(
    dsn=settings.sentry_dsn_server,
    environment=settings.environment.value,
    traces_sample_rate=0.1,
    release=__version__,
    integrations=[RedisIntegration()],
)

app = FastAPI(openapi_url=None)

app.add_middleware(SentryAsgiMiddleware)


@app.get("/admin")
async def get_admin():
    return RedirectResponse("/admin/", status_code=status.HTTP_308_PERMANENT_REDIRECT)


app.mount("/admin/api", api_app)
app.mount("/admin", dashboard_app)
app.mount("/", auth_app)


@app.on_event("startup")
async def on_startup():
    init_audit_logger(
        main_async_session_maker,
        functools.partial(
            get_workspace_session, workspace_engine_manager=workspace_engine_manager
        ),
    )
    logger.info("Fief Server started", version=__version__)


@app.on_event("shutdown")
async def on_shutdown():
    await workspace_engine_manager.close_all()


__all__ = ["app"]
