import asyncio
import os
import sys
from base64 import b64encode
from decimal import Decimal
from json import dumps
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import threeds
from redsys.clients import (
    MERCHANT_PARAMETERS,
    SIGNATURE,
    SIGNATURE_VERSION,
    AsyncDirectClient,
    DirectClient,
    RedirectClient,
)
from redsys.crypto import HMAC_SHA512_V1, get_signer
from redsys.exceptions import ResponseError, ValidationError
from redsys.models import decode_merchant_parameters

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
ORDER = '000000001'
OPERATION = dict(order=ORDER, amount=Decimal('10.56'))
DIRECT_CLIENTS = [DirectClient, AsyncDirectClient]


def _client(cls=DirectClient):
    return cls(SECRET, merchant_code='999008881', terminal=1, sandbox=True)


def _params(request):
    return decode_merchant_parameters(request.to_dict()[MERCHANT_PARAMETERS].encode())


# == Named operations ==


@pytest.mark.parametrize('client_class', DIRECT_CLIENTS)
@pytest.mark.parametrize(
    'method, transaction_type',
    [
        ('authentication', 7),
        ('authentication_confirmation', 8),
        ('pay_gold', 15),
        ('authentication_confirmation_cancellation', 47),
        ('partial_confirmation', 48),
    ],
)
def test_named_operation_sends_its_type_to_the_rest_endpoint(client_class, method, transaction_type):
    client = _client(client_class)
    request = getattr(client, method)(**OPERATION)
    assert _params(request)['Ds_Merchant_TransactionType'] == transaction_type
    assert request.endpoint == client.endpoint


@pytest.mark.parametrize('method', ['payment', 'preauthorization', 'confirmation', 'refund', 'void', 'pay_gold'])
@pytest.mark.parametrize('name', ['transaction_type', 'Ds_Merchant_TransactionType'])
def test_a_named_operation_rejects_a_different_type(method, name):
    with pytest.raises(ValidationError, match=name):
        getattr(_client(), method)(**OPERATION, **{name: 34})


def test_request_rejects_a_contradictory_type():
    with pytest.raises(ValidationError):
        client = RedirectClient(SECRET, merchant_code='999008881', terminal=1)
        client.request(0, Ds_Merchant_TransactionType=1, **OPERATION)


@pytest.mark.parametrize('value', [3, '3'])
@pytest.mark.parametrize('name', ['transaction_type', 'Ds_Merchant_TransactionType'])
def test_the_same_type_is_accepted_without_a_stray_key(name, value):
    params = _params(_client().refund(**OPERATION, **{name: value}))
    assert params['Ds_Merchant_TransactionType'] == 3
    assert all(key.startswith('Ds_') for key in params)


# == 3-D Secure ==


@pytest.mark.parametrize(
    'method, transaction_type',
    [('inicia_payment', 0), ('inicia_preauthorization', 1), ('inicia_authentication', 7)],
)
def test_inicia_variant_requests_the_card_data_by_default(method, transaction_type):
    client = _client()
    request = getattr(client, method)(**OPERATION)
    params = _params(request)
    assert params['Ds_Merchant_TransactionType'] == transaction_type
    assert params['Ds_Merchant_EMV3DS'] == threeds.card_data()
    assert request.endpoint == client.inicia_endpoint


@pytest.mark.parametrize('name', ['emv3ds', 'Ds_Merchant_EMV3DS'])
def test_inicia_variant_keeps_the_given_emv3ds(name):
    emv3ds = {'threeDSInfo': 'CardData', 'extra': 'kept'}
    params = _params(_client().inicia_payment(**OPERATION, **{name: emv3ds}))
    assert params['Ds_Merchant_EMV3DS'] == emv3ds
    assert all(key.startswith('Ds_') for key in params)


def test_inicia_variant_rejects_a_different_type():
    with pytest.raises(ValidationError):
        _client().inicia_payment(**OPERATION, transaction_type=1)


def test_inicia_keeps_its_behavior():
    params = _params(_client().inicia(**OPERATION, transaction_type=1))
    assert params['Ds_Merchant_TransactionType'] == 1
    assert 'Ds_Merchant_EMV3DS' not in params


@pytest.mark.parametrize('options, transaction_type', [({}, 0), ({'transaction_type': 1}, 1)])
def test_challenge_response_sets_the_step_and_keeps_the_type(options, transaction_type):
    client = _client()
    request = client.challenge_response(cres='abc', protocol_version='2.1.0', **OPERATION, **options)
    params = _params(request)
    assert params['Ds_Merchant_TransactionType'] == transaction_type
    assert params['Ds_Merchant_EMV3DS'] == threeds.challenge_response(cres='abc', protocol_version='2.1.0')
    assert request.endpoint == client.endpoint


@pytest.mark.parametrize('name', ['emv3ds', 'Ds_Merchant_EMV3DS'])
def test_challenge_response_rejects_its_own_emv3ds(name):
    with pytest.raises(ValidationError):
        _client().challenge_response(cres='abc', protocol_version='2.1.0', **OPERATION, **{name: {}})


# == Transport metadata ==


def _signed_body():
    merchant_parameters = b64encode(dumps({'Ds_Response': '0000', 'Ds_Order': ORDER, 'Ds_Amount': '1056'}).encode())
    return {
        SIGNATURE_VERSION: HMAC_SHA512_V1,
        MERCHANT_PARAMETERS: merchant_parameters.decode(),
        SIGNATURE: get_signer(SECRET, HMAC_SHA512_V1).sign(ORDER, merchant_parameters).decode(),
    }


def _http_response(httpx, status, body):
    request = httpx.Request('POST', 'https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST')
    return httpx.Response(status, json=body, headers={'X-Trace': 'abc'}, request=request)


def test_send_exposes_the_http_exchange():
    httpx = pytest.importorskip('httpx')
    http_response = _http_response(httpx, 200, _signed_body())
    with mock.patch('httpx.post', return_value=http_response):
        response = _client().refund(**OPERATION).send()
    assert response.is_refunded() or response.is_paid()
    assert response.http_status == 200
    assert response.http_headers['x-trace'] == 'abc'
    assert response.raw_body == http_response.text


def test_transport_metadata_stay_out_of_the_wire_fields():
    httpx = pytest.importorskip('httpx')
    with mock.patch('httpx.post', return_value=_http_response(httpx, 200, _signed_body())):
        response = _client().refund(**OPERATION).send()
    assert not {'http_status', 'http_headers', 'raw_body'} & set(response.model_dump())
    assert 'x-trace' not in repr(response)


def test_async_send_exposes_the_http_exchange():
    httpx = pytest.importorskip('httpx')
    http_response = _http_response(httpx, 200, _signed_body())
    http_client = mock.MagicMock()
    http_client.__aenter__ = mock.AsyncMock(return_value=http_client)
    http_client.__aexit__ = mock.AsyncMock(return_value=None)
    http_client.post = mock.AsyncMock(return_value=http_response)
    with mock.patch('httpx.AsyncClient', return_value=http_client):
        response = asyncio.run(_client(AsyncDirectClient).refund(**OPERATION).send())
    assert (response.http_status, response.raw_body) == (200, http_response.text)


def test_response_error_exposes_the_http_exchange():
    httpx = pytest.importorskip('httpx')
    http_response = _http_response(httpx, 200, {'errorCode': 'SIS0042'})
    with mock.patch('httpx.post', return_value=http_response), pytest.raises(ResponseError) as caught:
        _client().refund(**OPERATION).send()
    assert caught.value.error_code == 'SIS0042'
    assert caught.value.http_status == 200
    assert caught.value.http_headers['x-trace'] == 'abc'
    assert caught.value.raw_body == http_response.text


def test_http_errors_still_raise_from_httpx():
    httpx = pytest.importorskip('httpx')
    with mock.patch('httpx.post', return_value=_http_response(httpx, 502, {})), pytest.raises(httpx.HTTPStatusError):
        _client().refund(**OPERATION).send()


def test_parse_response_alone_leaves_the_metadata_empty():
    response = _client().parse_response(_signed_body())
    assert (response.http_status, response.http_headers, response.raw_body) == (None, None, None)
    with pytest.raises(ResponseError) as caught:
        _client().parse_response({'errorCode': 'SIS0042'})
    assert (caught.value.http_status, caught.value.http_headers, caught.value.raw_body) == (None, None, None)
