from fastapi import Depends, FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from fief.apps.dashboard.dependencies import BaseContext, get_base_context
from fief.apps.dashboard.exception_handlers import exception_handlers
from fief.apps.dashboard.routers.api_keys import router as api_keys_router
from fief.apps.dashboard.routers.auth import router as auth_router
from fief.apps.dashboard.routers.clients import router as clients_router
from fief.apps.dashboard.routers.email_templates import router as email_templates_router
from fief.apps.dashboard.routers.oauth_providers import router as oauth_providers_router
from fief.apps.dashboard.routers.permissions import router as permissions_router
from fief.apps.dashboard.routers.roles import router as roles_router
from fief.apps.dashboard.routers.tenants import router as tenants_router
from fief.apps.dashboard.routers.themes import router as themes_router
from fief.apps.dashboard.routers.user_fields import router as user_fields_router
from fief.apps.dashboard.routers.users import router as users_router
from fief.apps.dashboard.routers.webhooks import router as webhooks_router
from fief.dependencies.admin_authentication import is_authenticated_admin_session
from fief.middlewares.csrf import CSRFCookieSetterMiddleware
from fief.middlewares.security_headers import SecurityHeadersMiddleware
from fief.paths import STATIC_DIRECTORY
from fief.settings import settings
from fief.templates import templates

app = FastAPI(title="Fief Administration Dashboard", openapi_url=None)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFCookieSetterMiddleware)
app.add_middleware(GZipMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret.get_secret_value(),
    session_cookie=settings.session_data_cookie_name,
    max_age=settings.session_data_cookie_lifetime_seconds,
    https_only=settings.session_data_cookie_secure,
)

app.include_router(permissions_router, prefix="/access-control/permissions")
app.include_router(roles_router, prefix="/access-control/roles")
app.include_router(api_keys_router, prefix="/api-keys")
app.include_router(auth_router, prefix="/auth")
app.include_router(clients_router, prefix="/clients")
app.include_router(email_templates_router, prefix="/customization/email-templates")
app.include_router(themes_router, prefix="/customization/themes")
app.include_router(oauth_providers_router, prefix="/oauth-providers")
app.include_router(tenants_router, prefix="/tenants")
app.include_router(user_fields_router, prefix="/user-fields")
app.include_router(users_router, prefix="/users")
app.include_router(webhooks_router, prefix="/webhooks")
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="dashboard:static")

for exc, handler in exception_handlers.items():
    app.add_exception_handler(exc, handler)


@app.get(
    "/", name="dashboard:index", dependencies=[Depends(is_authenticated_admin_session)]
)
async def index(request: Request, context: BaseContext = Depends(get_base_context)):
    return templates.TemplateResponse(request, "admin/index.html", {**context})


__all__ = ["app"]
