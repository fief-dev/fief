import gettext
from typing import Dict, List

from babel import core

from fief.paths import LOCALE_DIRECTORY

Translations = gettext.NullTranslations

LOCALES = ["en_US", "fr_FR"]
FALLBACK = "en_US"
TERRITORY_FALLBACKS = {"en_US": "en", "fr_FR": "fr"}
SUPPORTED_LOCALES = LOCALES + list(TERRITORY_FALLBACKS.values())

TRANSLATIONS: Dict[str, Translations] = {}
for locale in LOCALES:
    translation = gettext.translation(
        domain="messages",
        localedir=LOCALE_DIRECTORY,
        languages=[locale],
        fallback=True,
    )
    TRANSLATIONS[locale] = translation
    try:
        TRANSLATIONS[TERRITORY_FALLBACKS[locale]] = translation
    except KeyError:
        pass


def get_preferred_locale(
    preffered: List[str],
    *,
    supported: List[str] = SUPPORTED_LOCALES,
    fallback: str = FALLBACK
) -> str:
    locale = core.negotiate_locale(preffered, supported)
    if locale is None:
        return fallback
    return locale


def get_preferred_translations(
    preffered: List[str],
    *,
    supported: List[str] = SUPPORTED_LOCALES,
    fallback: str = FALLBACK
) -> Translations:
    locale = get_preferred_locale(preffered, supported=supported, fallback=fallback)
    return TRANSLATIONS[locale]
