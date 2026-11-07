"""Meanings of RedSys result and error codes, in Spanish, Catalan, Galician, Basque or English.

from redsys.codes import describe

describe('0195', 'en')    # Ds_Response
describe('SIS0051')       # SIS error code
describe('BIZ00009')      # Bizum Request-to-Pay code
"""

from re import fullmatch

from redsys import _code_texts
from redsys.api import languages, responses

# Position of each language in the (Spanish, Catalan, Galician, Basque, English) texts; Valencian reads the Catalan.
_TEXT_INDEX = {
    'es': 0,
    'ca': 1,
    'va': 1,
    'gl': 2,
    'eu': 3,
    'en': 4,
    languages.SPANISH: 0,
    languages.CATALAN: 1,
    languages.VALENCIAN: 1,
    languages.GALICIAN: 2,
    languages.EUSKERA: 3,
    languages.ENGLISH: 4,
}


def _language_index(language) -> int | None:
    if isinstance(language, str):
        language = int(language) if language.isdigit() else language.lower()
    return _TEXT_INDEX.get(language)


def _texts(code) -> tuple[str, ...] | None:
    if isinstance(code, bool):
        return None
    if isinstance(code, int):
        code = str(code)
    if not isinstance(code, str):
        return None
    code = code.strip().upper()
    if match := fullmatch(r'SIS([0-9]{4})', code):
        return _code_texts.SIS.get(int(match.group(1)))
    if match := fullmatch(r'BIZ([0-9]{5})', code):
        return _code_texts.BIZ.get(int(match.group(1)))
    if not fullmatch(r'[0-9]{1,4}', code):
        return None
    number = int(code)
    if number <= responses.AUTHORIZED_LAST:
        return _code_texts.AUTHORIZED
    if number in _code_texts.DS_RESPONSE:
        return _code_texts.DS_RESPONSE[number]
    # Every SIS0nnn error has a numeric twin 9nnn that can arrive in Ds_Response.
    return _code_texts.SIS.get(number - 9000) if number >= 9000 else None


def describe(code, language='es') -> str:
    """The meaning of a ``Ds_Response`` code, an ``SISnnnn`` error code or a Bizum ``BIZnnnnn`` code.

    ``code`` is an ``int`` or a ``str`` (``0``, ``'0000'``, ``'SIS0051'``, ``'BIZ00009'``). ``language``
    is an ISO code (``'es'``, ``'en'``, ``'ca'``, ``'gl'``, ``'eu'``; ``'va'`` reads the Catalan) or RedSys's numeric
    one (``languages.SPANISH``, ``ENGLISH``, ``CATALAN``, ``VALENCIAN``, ``GALICIAN``, ``EUSKERA``).
    Returns ``''`` for an unknown code or language.
    """
    texts = _texts(code)
    index = _language_index(language)
    if texts is None or index is None:
        return ''
    return texts[index]


__all__ = ['describe']
