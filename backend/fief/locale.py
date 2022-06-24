import asgi_babel
from babel import support

Translations = support.Translations


def gettext_lazy(string: str, domain: str = None, **variables):
    return support.LazyProxy(asgi_babel.gettext, string, domain, **variables)


get_translations = asgi_babel.get_translations
