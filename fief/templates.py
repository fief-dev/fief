from typing import Any

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context, runtime
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.routing import Router

from fief.locale import get_translations
from fief.services.oauth_provider import get_oauth_provider_branding
from fief.services.posthog import POSTHOG_API_KEY
from fief.settings import settings


@pass_context
def get_column_macro(context: runtime.Context, column):
    column.renderer_macro = context[column.renderer_macro]
    return column


class LocaleJinja2Templates(Jinja2Templates):
    def _create_env(self, directory):
        env = super()._create_env(directory)
        env.add_extension("jinja2.ext.i18n")

        @pass_context
        def url_path_for(context: dict, name: str, **path_params: Any) -> str:
            router: Router = context["request"].scope["router"]
            return str(router.url_path_for(name, **path_params))

        env.globals["url_path_for"] = url_path_for
        env.globals["get_oauth_provider_branding"] = get_oauth_provider_branding
        env.globals["posthog_api_key"] = (
            POSTHOG_API_KEY if settings.telemetry_enabled else None
        )
        env.filters["get_column_macro"] = get_column_macro
        env.install_gettext_translations(get_translations(), newstyle=True)

        return env

    def TemplateResponse(  # type: ignore
        self,
        request: Request,
        name: str,
        context: dict | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        self.env.install_gettext_translations(get_translations(), newstyle=True)  # type: ignore
        return super().TemplateResponse(
            request=request,
            name=name,
            context=context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


templates = LocaleJinja2Templates(directory=settings.get_templates_directory())
