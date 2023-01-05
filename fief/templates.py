from collections.abc import Mapping
from typing import Any

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context, runtime
from starlette.background import BackgroundTask
from starlette.routing import Router

from fief.locale import get_translations
from fief.paths import TEMPLATES_DIRECTORY
from fief.services.oauth_provider import get_oauth_provider_branding


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
        env.filters["get_column_macro"] = get_column_macro
        env.install_gettext_translations(get_translations(), newstyle=True)  # type: ignore

        return env

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        self.env.install_gettext_translations(get_translations(), newstyle=True)  # type: ignore
        return super().TemplateResponse(
            name, context, status_code, headers, media_type, background
        )


templates = LocaleJinja2Templates(directory=TEMPLATES_DIRECTORY)
