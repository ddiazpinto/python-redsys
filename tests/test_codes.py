import os
import re
import sys
from base64 import b64encode
from json import dumps

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import languages, responses
from redsys.codes import describe
from redsys.models import Response

DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'response-codes.md')
AUTHORIZED_EN = 'Approved payment or pre-authorization'


def _doc_rows():
    with open(DOC, encoding='utf-8') as doc:
        return re.findall(r'^\| `([0-9A-Z-`]+)` \| (?:`([A-Z0-9_]+)` \| )?([^|]+?) \|$', doc.read(), re.M)


@pytest.mark.parametrize('code', [0, '0', '0000', '0042', 99, '0099'])
def test_codes_0_to_99_share_the_authorized_text(code):
    assert describe(code, 'en') == AUTHORIZED_EN
    assert describe(code) == 'Pago o preautorización aprobados'


@pytest.mark.parametrize('code', [195, '195', '0195', ' 0195 '])
def test_ds_response_accepts_int_and_str(code):
    assert describe(code, 'en') == 'Soft decline: SCA authentication required'


@pytest.mark.parametrize('language', ['es', 'ES', 1, '1', '001', languages.SPANISH])
def test_spanish_by_iso_or_redsys_code(language):
    assert describe('0116', language) == 'Saldo insuficiente'


@pytest.mark.parametrize('language', ['en', 'EN', 2, '2', languages.ENGLISH])
def test_english_by_iso_or_redsys_code(language):
    assert describe('0116', language) == 'Insufficient funds'


def test_spanish_is_the_default():
    assert describe('SIS0051') == describe('SIS0051', 'es') != describe('SIS0051', 'en')


def test_sis_and_bizum_codes():
    assert describe('SIS0042', 'en')
    assert describe('sis0042', 'en') == describe('SIS0042', 'en')
    assert describe('BIZ00009', 'en') == 'Payer not found (customer has no Bizum)'
    assert describe('SIS0001', 'en') == 'Unspecified internal error; contact RedSys support'


def test_a_9nnn_code_without_its_own_entry_falls_back_to_the_sis_text():
    assert describe(9051, 'en') == describe('SIS0051', 'en') != ''
    assert describe('9568', 'en') == describe('SIS0568', 'en')
    assert describe(9093, 'en') == 'Card does not exist' != describe('SIS0093', 'en')


@pytest.mark.parametrize(
    'code', ['0105', 105, 9000, '99999', 'SIS9999', 'SIS51', 'BIZ00004', 'BIZ0000', '', 'abc', None, True, -1, 1.5]
)
def test_unknown_code_is_empty(code):
    assert describe(code, 'en') == ''


@pytest.mark.parametrize('language', ['fr', 3, '', None, 'english'])
def test_unknown_language_is_empty(language):
    assert describe('0116', language) == ''


def test_texts_use_us_spelling():
    assert describe('9915', 'en') == 'Payment canceled by the user'


def test_every_code_in_the_doc_has_the_same_english_text():
    rows = _doc_rows()
    assert len(rows) > 80
    for code, constant, text in rows:
        first = code.split('`')[0]
        assert describe(first, 'en') == text, code
        if constant:
            assert describe(getattr(responses, constant), 'en') == text, constant


def test_every_named_response_code_is_described_and_listed():
    assert len(set(responses.RESPONSE_CODES)) == len(responses.RESPONSE_CODES)
    documented = {code.split('`')[0] for code, _, _ in _doc_rows()}
    for code in responses.RESPONSE_CODES:
        assert describe(code, 'en'), code
        assert f'{code:04d}' in documented, code


def _response(**fields):
    return Response.from_merchant_parameters(b64encode(dumps(fields).encode('utf-8')))


def test_response_describe():
    assert _response(Ds_Response='0195', Ds_Order='1').describe('en') == describe('0195', 'en')
    assert _response(Ds_Response='0195', Ds_Order='1').describe() == describe('0195', 'es')
    assert _response(Ds_ErrorCode='SIS0051', Ds_Order='1').describe('en') == describe('SIS0051', 'en')
    assert _response(Ds_Order='1').describe() == ''


def test_response_predicates_use_the_named_codes():
    assert _response(Ds_Response=f'{responses.REFUND_OR_CONFIRMATION_AUTHORIZED:04d}').is_refunded()
    assert _response(Ds_Response=f'{responses.CANCELLATION_AUTHORIZED:04d}').is_canceled()
