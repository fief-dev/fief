import gettext

from fastapi.templating import Jinja2Templates

translations = gettext.translation(
    domain="auth", localedir="locale", languages=["en_US"]
)
translations.install()

templates = Jinja2Templates(directory="templates")
templates.env.add_extension("jinja2.ext.i18n")
templates.env.install_gettext_translations(translations, newstyle=True)  # type: ignore
