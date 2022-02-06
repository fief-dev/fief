import gettext

from fastapi.templating import Jinja2Templates

from fief.paths import LOCALE_DIRECTORY, TEMPLATES_DIRECTORY

translations = gettext.translation(
    domain="auth", localedir=LOCALE_DIRECTORY, languages=["en_US"], fallback=True
)
translations.install()

templates = Jinja2Templates(directory=TEMPLATES_DIRECTORY)
templates.env.add_extension("jinja2.ext.i18n")
templates.env.install_gettext_translations(translations, newstyle=True)  # type: ignore
