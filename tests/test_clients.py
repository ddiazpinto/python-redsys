import os
import re
import sys
from base64 import b64decode, b64encode
from decimal import ROUND_HALF_UP, Decimal
from json import dumps, loads

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys.api import transactions
from redsys.clients import (
    DEFAULT_MODULE,
    MERCHANT_PARAMETERS,
    SIGNATURE,
    SIGNATURE_VERSION,
    DirectClient,
    RedirectClient,
)
from redsys.crypto import HMAC_SHA256_V1, HMAC_SHA512_V1, HMAC_SHA512_V2, get_signer

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
ORDER = '000000001'


def _client(**overrides):
    params = dict(merchant_code='999008881', terminal=1, sandbox=True)
    params.update(overrides)
    return RedirectClient(SECRET, **params)


def _decoded(prepared):
    data = prepared.to_dict()[MERCHANT_PARAMETERS].replace('-', '+').replace('_', '/')
    return loads(b64decode(data + '=' * (-len(data) % 4)).decode('utf-8'))


def _signed_response(version):
    params = {'Ds_Response': '0000', 'Ds_Order': ORDER, 'Ds_Amount': '1056'}
    merchant_parameters = b64encode(dumps(params).encode('utf-8'))
    signature = get_signer(SECRET, version).sign(ORDER, merchant_parameters)
    return {
        SIGNATURE_VERSION: version,
        MERCHANT_PARAMETERS: merchant_parameters.decode('utf-8'),
        SIGNATURE: signature.decode('utf-8'),
    }


def _roundtrip(version):
    client = _client(signature_version=version)
    prepared = client.payment(
        order=ORDER,
        currency=978,
        amount=Decimal('10.56489').quantize(Decimal('.01'), ROUND_HALF_UP),
        merchant_url='https://example.com/notify',
    )
    assert _decoded(prepared)['Ds_Merchant_Amount'] == 1056
    assert prepared.to_dict()[SIGNATURE_VERSION] == version

    response = client.parse_response(_signed_response(version))
    assert response.is_paid()
    assert response.order == ORDER
    assert response.amount == Decimal('10.56')


def test_roundtrip_sha256_v1():
    _roundtrip(HMAC_SHA256_V1)


def test_roundtrip_sha512_v1():
    _roundtrip(HMAC_SHA512_V1)


def test_default_signature_version_is_sha512_v2():
    prepared = _client().payment(order=ORDER, currency=978, amount=Decimal('10.56'))
    assert prepared.to_dict()[SIGNATURE_VERSION] == HMAC_SHA512_V2
    assert '=' not in prepared.to_dict()[MERCHANT_PARAMETERS]  # unpadded Base64URL under V2


def test_client_injects_merchant_code_and_terminal():
    decoded = _decoded(_client(terminal=7).payment(order=ORDER, currency=978, amount=Decimal('10.56')))
    assert decoded['Ds_Merchant_MerchantCode'] == '999008881'
    assert decoded['Ds_Merchant_Terminal'] == 7


def test_per_call_terminal_overrides_client_default():
    decoded = _decoded(_client(terminal=1).payment(order=ORDER, currency=978, amount=Decimal('10.56'), terminal=2))
    assert decoded['Ds_Merchant_Terminal'] == 2


def test_named_operation_sets_transaction_type():
    payment = _decoded(_client().payment(order=ORDER, currency=978, amount=Decimal('1.00')))
    assert payment['Ds_Merchant_TransactionType'] == 0
    preauth = _decoded(_client().preauthorization(order=ORDER, currency=978, amount=Decimal('1.00')))
    assert preauth['Ds_Merchant_TransactionType'] == 1


def test_low_level_request_reaches_undecorated_transaction_type():
    client = DirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)
    decoded = _decoded(client.request(transactions.REFUND_CANCELLATION, order=ORDER, amount=Decimal('1.00')))
    assert decoded['Ds_Merchant_TransactionType'] == 46


def test_tampered_signature_rejected():
    payload = _signed_response(HMAC_SHA512_V1)
    payload[SIGNATURE] = 'tampered'
    try:
        _client().parse_response(payload)
        raise AssertionError('expected ValueError for tampered signature')
    except ValueError:
        pass


def test_redirect_request_cannot_be_sent():
    prepared = _client().payment(order=ORDER, currency=978, amount=Decimal('10.56'))
    try:
        prepared.send()
        raise AssertionError('expected TypeError: redirect requests are browser-submitted')
    except TypeError:
        pass


def test_direct_client_endpoints_not_inverted():
    assert DirectClient(SECRET).endpoint == 'https://sis.redsys.es/sis/rest/trataPeticionREST'
    assert DirectClient(SECRET, sandbox=True).endpoint == 'https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST'


def test_currency_defaults_to_euro():
    params = _decoded(_client().payment(order=ORDER, amount=Decimal('10.56')))
    assert params['Ds_Merchant_Currency'] == 978
    assert params['Ds_Merchant_Amount'] == 1056


def test_client_currency_sets_the_default_and_scales_the_amount():
    params = _decoded(_client(currency=392).payment(order=ORDER, amount=Decimal('1000')))
    assert params['Ds_Merchant_Currency'] == 392
    assert params['Ds_Merchant_Amount'] == 1000


def test_call_currency_wins_over_the_client_default():
    params = _decoded(_client(currency=392).payment(order=ORDER, currency=978, amount=Decimal('10.56')))
    assert params['Ds_Merchant_Currency'] == 978
    assert params['Ds_Merchant_Amount'] == 1056


def test_wire_name_wins_over_client_defaults_without_stray_keys():
    client = _client(currency=392)
    params = _decoded(
        client.payment(
            order=ORDER,
            amount=Decimal('10.56'),
            Ds_Merchant_Currency=978,
            Ds_Merchant_MerchantCode='111111111',
            Ds_Merchant_Terminal=2,
        )
    )
    assert params['Ds_Merchant_Currency'] == 978
    assert params['Ds_Merchant_MerchantCode'] == '111111111'
    assert params['Ds_Merchant_Terminal'] == 2
    assert all(key.startswith('Ds_') for key in params)


# == Module id ==


def test_requests_carry_the_library_module_by_default():
    params = _decoded(_client().payment(order=ORDER, amount=Decimal('10.56')))
    assert params['Ds_Merchant_Module'] == DEFAULT_MODULE
    assert re.fullmatch(r'python-redsys/[0-9]+\.[0-9]+\.[0-9]+.*', DEFAULT_MODULE)


def test_direct_and_api_key_clients_carry_the_module_too():
    direct = DirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)
    assert _decoded(direct.refund(order=ORDER, amount=Decimal('1')))['Ds_Merchant_Module'] == DEFAULT_MODULE
    api_key = 'TEST_OTk5MDA4ODgxXzAwMV9zcTdIanJVT0JmS21DNTc2SUxnc2tENXNyVTg3MGdKNw'
    assert DirectClient.from_api_key(api_key, module='shop/1.0').module == 'shop/1.0'


def test_client_module_replaces_the_default_and_a_call_wins():
    client = _client(module='shop/1.0')
    assert _decoded(client.payment(order=ORDER, amount=Decimal('1')))['Ds_Merchant_Module'] == 'shop/1.0'
    assert _decoded(client.payment(order=ORDER, amount=Decimal('1'), module='x'))['Ds_Merchant_Module'] == 'x'
    by_wire_name = _decoded(client.payment(order=ORDER, amount=Decimal('1'), Ds_Merchant_Module='y'))
    assert by_wire_name['Ds_Merchant_Module'] == 'y' and 'module' not in by_wire_name


def test_module_none_leaves_the_parameter_out():
    assert 'Ds_Merchant_Module' not in _decoded(_client(module=None).payment(order=ORDER, amount=Decimal('1')))
    assert 'Ds_Merchant_Module' not in _decoded(_client().payment(order=ORDER, amount=Decimal('1'), module=None))


def test_module_without_package_metadata_names_only_the_library():
    from importlib.metadata import PackageNotFoundError
    from unittest import mock

    from redsys import clients

    with mock.patch.object(clients, 'version', side_effect=PackageNotFoundError):
        assert clients._default_module() == 'python-redsys'
