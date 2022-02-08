from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTasks

from fief.locale import Translations
from fief.paths import TEMPLATES_DIRECTORY


class LocaleJinja2Templates(Jinja2Templates):
    def _create_env(self, directory):
        env = super()._create_env(directory)
        env.add_extension("jinja2.ext.i18n")
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
