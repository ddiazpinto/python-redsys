"""Meanings of RedSys result and error codes, in Spanish or English.

from redsys.codes import describe

describe('0195', 'en')    # Ds_Response
describe('SIS0051')       # SIS error code
describe('BIZ00009')      # Bizum Request-to-Pay code
"""

from re import fullmatch

from redsys import _code_texts
from redsys.api import responses

# Position of each language in the (English, Spanish) text pairs.
_TEXT_INDEX = {'en': 0, 'es': 1, 2: 0, 1: 1}


def _language_index(language) -> int | None:
    if isinstance(language, str):
        language = int(language) if language.isdigit() else language.lower()
    return _TEXT_INDEX.get(language)


def _texts(code) -> tuple[str, str] | None:
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
    is ``'es'`` or ``'en'``, or RedSys's numeric code (``languages.SPANISH``, ``languages.ENGLISH``).
    Returns ``''`` for an unknown code or language.
    """
    texts = _texts(code)
    index = _language_index(language)
    if texts is None or index is None:
        return ''
    return texts[index]


__all__ = ['describe']
