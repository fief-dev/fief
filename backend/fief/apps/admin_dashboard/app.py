from fastapi import Depends, FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from fief.apps.admin_dashboard.dependencies import BaseContext, get_base_context
from fief.apps.admin_dashboard.routers.auth import router as auth_router
from fief.apps.admin_dashboard.routers.clients import router as clients_router
from fief.apps.admin_dashboard.routers.tenants import router as tenants_router
from fief.paths import STATIC_DIRECTORY
from fief.templates import templates

app = FastAPI(title="Fief Administration Dashboard", openapi_url=None)

app.add_middleware(GZipMiddleware)

app.include_router(auth_router, prefix="/auth")
app.include_router(clients_router, prefix="/clients")
app.include_router(tenants_router, prefix="/tenants")
app.mount(
    "/static", StaticFiles(directory=STATIC_DIRECTORY), name="admin_dashboard:static"
)


@app.get("/")
async def index(context: BaseContext = Depends(get_base_context)):
    return templates.TemplateResponse("admin/index.html", {**context})


__all__ = ["app"]
