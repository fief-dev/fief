from typing import Any

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from pycountry import countries
from pytz import common_timezones
from starlette.background import BackgroundTasks
from starlette.routing import Router

from fief.locale import Translations
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
        env.globals["countries"] = sorted(countries, key=lambda c: c.name)
        env.globals["timezones"] = sorted(common_timezones)

        return env

    def LocaleTemplateResponse(
        self,
        name: str,
        context: dict,
        translations: Translations,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTasks = None,
    ):
        self.env.install_gettext_translations(translations, newstyle=True)  # type: ignore
        return super().TemplateResponse(
            name, context, status_code, headers, media_type, background
        )


templates = LocaleJinja2Templates(directory=TEMPLATES_DIRECTORY)
