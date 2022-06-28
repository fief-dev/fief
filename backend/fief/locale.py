from typing import Any, Mapping

import asgi_babel
import wtforms.i18n
from babel import Locale, support

from fief.paths import LOCALE_DIRECTORY

Translations = support.Translations

BabelMiddleware = asgi_babel.BabelMiddleware


def get_babel_middleware_kwargs() -> Mapping[str, Any]:
    return dict(locales_dirs=[LOCALE_DIRECTORY, wtforms.i18n.messages_path()])


def gettext_lazy(string: str, domain: str = None, **variables):
    return support.LazyProxy(asgi_babel.gettext, string, domain, **variables)


def get_translations(domain: str = None, locale: Locale = None) -> support.Translations:
    """
    Load and cache translations.

    Patched version to prevent bug when then first loaded translation is Null.
    """
    from asgi_babel import BABEL, current_locale

    if BABEL is None:
        raise RuntimeError("BabelMiddleware is not inited.")  # noqa: TC003

    locale = locale or current_locale.get()
    if not locale:
        return support.NullTranslations()

    domain = domain or BABEL.domain
    if (domain, locale.language) not in BABEL.translations:
        translations = None
        for path in reversed(BABEL.locales_dirs):
            trans = support.Translations.load(path, locales=locale, domain=domain)
            if translations and not type(translations) == support.NullTranslations:
                translations._catalog.update(trans._catalog)
            else:
                translations = trans

        BABEL.translations[(domain, locale.language)] = translations

    return BABEL.translations[(domain, locale.language)]
