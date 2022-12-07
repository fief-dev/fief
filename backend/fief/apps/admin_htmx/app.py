from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles

from fief.apps.admin_htmx.routers.clients import router as clients_router
from fief.paths import STATIC_DIRECTORY
from fief.apps.admin_htmx.templates import templates
from fief.apps.admin_htmx.dependencies import BaseContext, get_base_context

app = FastAPI(title="Fief Administration Frontend", openapi_url=None)

app.include_router(clients_router, prefix="/clients")
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="admin_htmx:static")


@app.get("/")
async def index(context: BaseContext = Depends(get_base_context)):
    return templates.TemplateResponse("index.html", {**context})


__all__ = ["app"]
