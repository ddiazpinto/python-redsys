import os
import sys
from base64 import b64encode
from decimal import Decimal
from json import dumps, loads
from types import MappingProxyType
from unittest import mock

import httpx
import pytest
from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import clients
from redsys.clients import MERCHANT_PARAMETERS, SIGNATURE, SIGNATURE_VERSION, DirectClient, RedirectClient
from redsys.crypto import HMAC_SHA256_V1, HMAC_SHA512_V2, get_signer
from redsys.exceptions import ResponseError, ValidationError
from redsys.models import _MAX_JSON_DEPTH, Response, _json_depth_exceeds

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
ORDER = '000000001'


def _client():
    return RedirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)


def _encoded(raw: bytes) -> str:
    return b64encode(raw).decode('ascii')


def _payload(merchant_parameters, signature='x', version=HMAC_SHA512_V2) -> dict:
    return {SIGNATURE_VERSION: version, MERCHANT_PARAMETERS: merchant_parameters, SIGNATURE: signature}


def _signed(fields: dict, order: str = ORDER, version: str = HMAC_SHA256_V1) -> dict:
    merchant_parameters = b64encode(dumps(fields).encode('utf-8'))
    signature = get_signer(SECRET, version).sign(order, merchant_parameters)
    return _payload(merchant_parameters.decode('ascii'), signature.decode('ascii'), version)


def _nested(depth: int):
    value: list = []
    for _ in range(depth - 1):
        value = [value]
    return value


_UNSIGNED_FIELDS = _encoded(b'{"Ds_Order": "000000001", "Ds_Response": "0000"}')

MALFORMED = {
    'not a mapping': [MERCHANT_PARAMETERS],
    'neither parameters nor error code': {},
    'no signature': {MERCHANT_PARAMETERS: _UNSIGNED_FIELDS},
    'signature not text': _payload(_UNSIGNED_FIELDS, signature=7),
    'signature too long': _payload(_UNSIGNED_FIELDS, signature='A' * 129),
    'parameters not text': _payload(7),
    'parameters not ascii': _payload('\ud800' + _UNSIGNED_FIELDS),
    'unsupported version': _payload(_UNSIGNED_FIELDS, version='HMAC_MD5_V0'),
    'not base64 json': _payload('AAAA'),
    'not utf-8': _payload(_encoded(b'\xff\xfe')),
    'json array': _payload(_encoded(b'[1, 2]')),
    'order not encodable': _payload(_encoded(b'{"Ds_Order": "\\ud800"}')),
    'nested too deep': _payload(_encoded(dumps({'Ds_Order': ORDER, 'x': _nested(_MAX_JSON_DEPTH)}).encode())),
}


@pytest.mark.parametrize('payload', MALFORMED.values(), ids=MALFORMED.keys())
def test_malformed_payload_raises_validation_error(payload):
    with pytest.raises(ValidationError):
        _client().parse_response(payload)


def test_validation_error_is_a_value_error():
    with pytest.raises(ValueError):
        _client().parse_response(_payload('AAAA'))


def test_error_payload_still_raises_response_error():
    with pytest.raises(ResponseError):
        _client().parse_response({'Ds_ErrorCode': 'SIS0042'})


def test_oversized_parameters_are_rejected_before_decoding():
    payload = _signed({'Ds_Order': ORDER, 'Ds_Response': '0000'})
    with (
        mock.patch.object(clients, '_MAX_MERCHANT_PARAMETERS_LENGTH', len(payload[MERCHANT_PARAMETERS]) - 1),
        mock.patch.object(clients, 'decode_merchant_parameters') as decode,
        pytest.raises(ValidationError, match='exceeds'),
    ):
        _client().parse_response(payload)
    decode.assert_not_called()


def test_parameters_at_the_limit_are_accepted():
    payload = _signed({'Ds_Order': ORDER, 'Ds_Response': '0000'})
    with mock.patch.object(clients, '_MAX_MERCHANT_PARAMETERS_LENGTH', len(payload[MERCHANT_PARAMETERS])):
        assert _client().parse_response(payload).is_paid()


def test_deep_nesting_is_rejected_before_parsing():
    with (
        mock.patch('redsys.models.loads') as parse,
        pytest.raises(ValidationError, match='nests deeper'),
    ):
        _client().parse_response(MALFORMED['nested too deep'])
    parse.assert_not_called()


def test_nesting_at_the_limit_is_accepted():
    fields = {'Ds_Order': ORDER, 'Ds_Response': '0000', 'x': _nested(_MAX_JSON_DEPTH - 1)}
    assert _client().parse_response(_signed(fields)).is_paid()


@pytest.mark.parametrize(
    'text',
    [
        '{"a": "[[[[", "b": [1, {"c": "]]]]"}]}',
        '{"a": "x\\"[[", "b": "\\\\", "c": [[]], "d": "\\\\\\"]]"}',
        '{"Ds_MerchantData": "{\\"cart\\":[{\\"x\\":[1]}]}", "Ds_EMV3DS": {"a": [{"b": 1}]}}',
        '[' * 40 + ']' * 40,
        '{"a": "' + ']' * 40 + '", "b": ' + '[' * 30 + ']' * 30 + '}',
    ],
)
def test_depth_ignores_brackets_inside_strings(text):
    def depth(value):
        children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else ()
        return 1 + max(map(depth, children), default=0) if isinstance(value, (dict, list)) else 0

    actual = depth(loads(text))
    padded = ('[' + text + ',' + ','.join(['[]'] * 40) + ']').encode()
    assert _json_depth_exceeds(padded, actual + 1) is False
    assert _json_depth_exceeds(padded, actual) is True


@pytest.mark.parametrize('amount', ['1E99999999', 'not a number'])
def test_fields_are_not_validated_without_a_matching_signature(amount):
    payload = _payload(_encoded(dumps({'Ds_Order': ORDER, 'Ds_Amount': amount}).encode('utf-8')))
    with (
        mock.patch.object(Response, 'model_validate') as validate,
        pytest.raises(ValueError, match='Signature is not valid'),
    ):
        _client().parse_response(payload)
    validate.assert_not_called()


def test_missing_order_fails_verification():
    with pytest.raises(ValueError, match='Signature is not valid'):
        _client().parse_response(_signed({'Ds_Response': '0000'}))


def test_signed_invalid_field_raises_validation_error_with_the_cause():
    with pytest.raises(ValidationError) as raised:
        _client().parse_response(_signed({'Ds_Order': ORDER, 'Ds_Amount': 'not a number'}))
    assert isinstance(raised.value.__cause__, PydanticValidationError)


def test_signed_amount_out_of_range_raises_validation_error():
    with pytest.raises(ValidationError):
        _client().parse_response(_signed({'Ds_Order': ORDER, 'Ds_Amount': '1E99999999'}))


def test_well_formed_signed_payload_parses():
    response = _client().parse_response(_signed({'Ds_Order': ORDER, 'Ds_Response': '0000', 'Ds_Amount': '1056'}))
    assert response.is_paid()
    assert response.amount == Decimal('10.56')


@pytest.mark.parametrize('kind', [bytes, bytearray])
def test_binary_fields_are_accepted(kind):
    payload = _signed({'Ds_Order': ORDER, 'Ds_Response': '0000'})
    payload[MERCHANT_PARAMETERS] = kind(payload[MERCHANT_PARAMETERS].encode())
    payload[SIGNATURE] = kind(payload[SIGNATURE].encode())
    assert _client().parse_response(payload).is_paid()


def test_any_mapping_is_accepted():
    assert _client().parse_response(MappingProxyType(_signed({'Ds_Order': ORDER, 'Ds_Response': '0000'}))).is_paid()


def test_send_raises_validation_error_for_an_answer_that_is_not_json():
    client = DirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)
    request = client.payment(order=ORDER, amount=Decimal('1.00'))
    answer = httpx.Response(200, text='<html>busy</html>', request=httpx.Request('POST', request.endpoint))
    with mock.patch('httpx.post', return_value=answer), pytest.raises(ValidationError, match='not JSON'):
        request.send()
