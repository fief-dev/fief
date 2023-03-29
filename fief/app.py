import sentry_sdk
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.redis import RedisIntegration

from fief import __version__
from fief.apps import api_app, auth_app, dashboard_app
from fief.lifespan import lifespan
from fief.settings import settings

sentry_sdk.init(
    dsn=settings.sentry_dsn_server,
    environment=settings.environment.value,
    traces_sample_rate=0.1,
    release=__version__,
    integrations=[RedisIntegration()],
)

app = FastAPI(lifespan=lifespan, openapi_url=None)

app.add_middleware(SentryAsgiMiddleware)


@app.get("/admin")
async def get_admin():
    return RedirectResponse("/admin/", status_code=status.HTTP_308_PERMANENT_REDIRECT)


app.mount("/admin/api", api_app)
app.mount("/admin", dashboard_app)
app.mount("/", auth_app)

__all__ = ["app"]
