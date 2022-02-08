import operator
import re
from typing import List, Tuple

from fastapi import Depends, Header, Request

from fief.locale import FALLBACK, Translations, get_preferred_translations

ACCEPT_LANGUAGE_REGEX = re.compile(
    r"""
    (                       # media-range capturing-parenthesis
      [^\s;,]+              # type/subtype
      (?:[ \t]*;[ \t]*      # ";"
        (?:                 # parameter non-capturing-parenthesis
          [^\s;,q][^\s;,]*  # token that doesn't start with "q"
        |                   # or
          q[^\s;,=][^\s;,]* # token that is more than just "q"
        )
      )*                    # zero or more parameters
    )                       # end of media-range
    (?:[ \t]*;[ \t]*q=      # weight is a "q" parameter
      (\d*(?:\.\d+)?)       # qvalue capturing-parentheses
      [^,]*                 # "extension" accept params: who cares?
    )?                      # accept params are optional
    """,
    re.VERBOSE,
)


async def get_accepted_languages(accept_language: str = Header(None)) -> List[str]:
    if accept_language is None:
        return [FALLBACK]

    parsed_languages: List[Tuple[str, float]] = []
    for match in ACCEPT_LANGUAGE_REGEX.finditer(accept_language):
        language = match.group(1).replace("-", "_")
        quality = match.group(2)
        if quality is None:
            quality = 1.0
        else:
            quality = float(quality)
        parsed_languages.append((language, quality))

    sorted_languages = sorted(
        parsed_languages, key=operator.itemgetter(1), reverse=True
    )
    return [language for (language, _) in sorted_languages]


async def get_translations(
    request: Request,
    accepted_languages: List[str] = Depends(get_accepted_languages),
) -> Translations:
    translations = get_preferred_translations(accepted_languages)
    request.scope["translations"] = translations
    return translations


async def get_gettext(translations: Translations = Depends(get_translations)):
    return translations.gettext
