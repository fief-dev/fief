from typing import Any, Mapping, Optional

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from starlette.background import BackgroundTask
from starlette.routing import Router

from fief.locale import get_translations
from fief.paths import TEMPLATES_DIRECTORY


class LocaleJinja2Templates(Jinja2Templates):
    def _create_env(self, directory):
        env = super()._create_env(directory)
        env.add_extension("jinja2.ext.i18n")

        @pass_context
        def url_path_for(context: dict, name: str, **path_params: Any) -> str:
            router: Router = context["request"].scope["router"]
            return str(router.url_path_for(name, **path_params))

        env.globals["url_path_for"] = url_path_for

        return env

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ):
        self.env.install_gettext_translations(get_translations(), newstyle=True)  # type: ignore
        return super().TemplateResponse(
            name, context, status_code, headers, media_type, background
        )


templates = LocaleJinja2Templates(directory=TEMPLATES_DIRECTORY)
