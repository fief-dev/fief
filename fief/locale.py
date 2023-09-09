from collections.abc import Mapping
from typing import Any

import asgi_babel
import wtforms.i18n
from asgi_tools import Request
from babel import Locale, UnknownLocaleError, support

from fief.paths import LOCALE_DIRECTORY
from fief.settings import settings

Translations = support.Translations


async def select_locale(request: Request) -> str | None:
    user_locale_cookie = request.cookies.get(settings.user_locale_cookie_name)
    if user_locale_cookie is not None:
        try:
            Locale.parse(user_locale_cookie, sep="-")
        except (ValueError, UnknownLocaleError):
            pass
        else:
            return user_locale_cookie
    return await asgi_babel.select_locale_by_request(request)


class BabelMiddleware(asgi_babel.BabelMiddleware):
    def __post_init__(self):
        self.locale_selector = select_locale
        return super().__post_init__()


def get_babel_middleware_kwargs() -> Mapping[str, Any]:
    return dict(locales_dirs=[LOCALE_DIRECTORY, wtforms.i18n.messages_path()])


def get_translations(
    domain: str | None = None, locale: Locale | None = None
) -> support.NullTranslations:
    """
    Load and cache translations.

    Patched version to prevent bug when then first loaded translation is Null.
    """
    from asgi_babel import BABEL, current_locale

    if BABEL is None:
        return support.NullTranslations()

    locale = locale or current_locale.get()
    if not locale:
        return support.NullTranslations()

    domain = domain or BABEL.domain
    locale_code = str(locale)
    if (domain, locale_code) not in BABEL.translations:
        translations = None
        for path in reversed(BABEL.locales_dirs):
            trans = support.Translations.load(path, locales=locale_code, domain=domain)
            if translations and not type(translations) == support.NullTranslations:
                translations._catalog.update(trans._catalog)
            else:
                translations = trans

        BABEL.translations[(domain, locale_code)] = translations

    return BABEL.translations[(domain, locale_code)]


def gettext(string: str, domain: str | None = None, **variables):
    t = get_translations(domain)
    return t.ugettext(string) % variables


def gettext_lazy(string: str, domain: str | None = None, **variables):
    return support.LazyProxy(gettext, string, domain, **variables, enable_cache=False)
