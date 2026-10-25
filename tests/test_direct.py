import os
import sys
from base64 import b64encode
from decimal import Decimal
from json import dumps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import threeds
from redsys.clients import (
    DEFAULT_SIGNATURE_VERSION,
    MERCHANT_PARAMETERS,
    SIGNATURE,
    SIGNATURE_VERSION,
    AsyncDirectClient,
    DirectClient,
)
from redsys.crypto import HMAC_SHA512_V1, get_signer
from redsys.exceptions import ResponseError

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
ORDER = '000000001'

try:
    import httpx  # noqa: F401

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


def _client(cls=DirectClient, **overrides):
    params = dict(merchant_code='999008881', terminal=1, sandbox=True)
    params.update(overrides)
    return cls(SECRET, **params)


def _decoded_params(request):
    from redsys.models import decode_merchant_parameters

    return decode_merchant_parameters(request.merchant_parameters)


def _payment(client):
    return client.payment(
        order=ORDER,
        currency=978,
        amount=Decimal('10.56'),
        pan='4548810000000003',
        expiry_date='4912',
        cvv2='123',
    )


def _signed_response_payload(version=HMAC_SHA512_V1):
    params = {'Ds_Response': '0000', 'Ds_Order': ORDER, 'Ds_Amount': '1056'}
    merchant_parameters = b64encode(dumps(params).encode('utf-8'))
    signature = get_signer(SECRET, version).sign(ORDER, merchant_parameters)
    return {
        SIGNATURE_VERSION: version,
        MERCHANT_PARAMETERS: merchant_parameters.decode('utf-8'),
        SIGNATURE: signature.decode('utf-8'),
    }


def test_envelope_to_dict_has_three_wire_fields():
    body = _payment(_client()).to_dict()
    assert set(body) == {SIGNATURE_VERSION, MERCHANT_PARAMETERS, SIGNATURE}
    assert body[SIGNATURE_VERSION] == DEFAULT_SIGNATURE_VERSION
    assert isinstance(body[MERCHANT_PARAMETERS], str) and isinstance(body[SIGNATURE], str)


def test_parse_response_round_trip():
    response = _client().parse_response(_signed_response_payload())
    assert response.is_paid()
    assert response.amount == Decimal('10.56')
    assert response.order == ORDER


def test_parse_response_raises_on_error_payload():
    try:
        _client().parse_response({'errorCode': 'SIS0042'})
        raise AssertionError('expected ResponseError')
    except ResponseError as error:
        assert error.error_code == 'SIS0042'


def test_parse_response_rejects_tampered_signature():
    payload = _signed_response_payload()
    payload[SIGNATURE] = 'tampered'
    try:
        _client().parse_response(payload)
        raise AssertionError('expected ValueError')
    except ValueError:
        pass


def test_send_posts_signed_body_and_parses_response():
    if not HAS_HTTPX:
        print('skip test_send (httpx not installed)')
        return
    import httpx

    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return _signed_response_payload()

    def _fake_post(url, json=None, **kwargs):
        captured['url'] = url
        captured['json'] = json
        return _FakeResponse()

    original_post = httpx.post
    httpx.post = _fake_post
    try:
        response = _payment(_client(sandbox=False)).send()
    finally:
        httpx.post = original_post

    assert response.is_paid()
    assert captured['url'] == 'https://sis.redsys.es/sis/rest/trataPeticionREST'
    assert set(captured['json']) == {SIGNATURE_VERSION, MERCHANT_PARAMETERS, SIGNATURE}


def test_async_inicia_posts_and_parses():
    if not HAS_HTTPX:
        print('skip test_async_inicia (httpx not installed)')
        return
    import asyncio

    import httpx

    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return _signed_response_payload()

    class _FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return None

        async def post(self, url, json=None, **kwargs):
            captured['url'] = url
            captured['json'] = json
            return _FakeResponse()

    original = httpx.AsyncClient
    httpx.AsyncClient = _FakeAsyncClient
    try:
        prepared = _client(AsyncDirectClient).inicia(
            order=ORDER,
            currency=978,
            amount=Decimal('10.56'),
            pan='4548810000000003',
            expiry_date='4912',
            cvv2='123',
            emv3ds=threeds.card_data(),
        )
        response = asyncio.run(prepared.send())
    finally:
        httpx.AsyncClient = original

    assert response.is_paid()
    assert captured['url'] == 'https://sis-t.redsys.es:25443/sis/rest/iniciaPeticionREST'
    assert set(captured['json']) == {SIGNATURE_VERSION, MERCHANT_PARAMETERS, SIGNATURE}


def test_extra_transaction_types_build_on_their_message():
    from redsys import transactions

    client = DirectClient('sq7HjrUOBfKmC576ILgskD5srU870gJ7', merchant_code='999008881', terminal=1, sandbox=True)
    for code in (11, 44, 45, 46, 47, 48):
        assert code in transactions.TRANSACTION_TYPES
        request = client.request(code, order='000000000001', amount=Decimal('1.00'), currency=978)
        assert _decoded_params(request)['Ds_Merchant_TransactionType'] == code


def test_dcc_passes_through_request_and_response():
    client = DirectClient('sq7HjrUOBfKmC576ILgskD5srU870gJ7', merchant_code='999008881', terminal=1, sandbox=True)
    offer = {'monedaDCC': '840', 'importeDCC': '117'}
    request = client.payment(order='000000000001', amount=Decimal('1.00'), currency=978, dcc=offer)
    assert _decoded_params(request)['Ds_Merchant_DCC'] == offer
