from babel import Locale, support

Translations = support.Translations


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
            if translations and not isinstance(translations, support.NullTranslations):
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
