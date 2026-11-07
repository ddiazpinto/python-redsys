import os
import sys
import warnings
from decimal import Decimal

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import xpay
from redsys.clients import DirectClient
from redsys.models import (
    DirectPaymentMessage,
    DirectPreauthorizationMessage,
    RedirectPaymentMessage,
    decode_merchant_parameters,
)

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
BASE = dict(merchant_code='999008881', terminal=1, order='000000001', amount=Decimal('1.00'))
DECODED = {
    'token': '4548810000000003',
    'expirationDate': '4912',
    'paymentMethod': xpay.TOKENIZED_CARD,
    'cryptogram': 'AAAAAAAAAAAAAAAAAAAAAAAAAAA=',
    'eciInd': '05',
}


def _params(model, **fields):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        return model(**BASE, **fields).prepare_parameters()


@pytest.mark.parametrize('model', [DirectPaymentMessage, DirectPreauthorizationMessage])
def test_encrypted_wallet_payload(model):
    params = _params(model, xpay_data='7B2276657273696F6E223A7D', xpay_type=xpay.APPLE, xpay_origen=xpay.WEB)
    assert params['DS_XPAYDATA'] == '7B2276657273696F6E223A7D'
    assert (params['DS_XPAYTYPE'], params['DS_XPAYORIGEN']) == ('Apple', 'WEB')


def test_decoded_wallet_payload_by_wire_name():
    params = _params(DirectPaymentMessage, DS_XPAYDECODEDDATA=DECODED, DS_XPAYTYPE='Google', DS_XPAYORIGEN='InApp')
    assert params['DS_XPAYDECODEDDATA'] == DECODED
    assert not any(key.startswith('Ds_Merchant_X') for key in params)


def test_client_sends_the_wallet_fields():
    client = DirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)
    request = client.payment(
        order='000000001', amount=Decimal('1.00'), xpay_data='abc', xpay_type=xpay.GOOGLE, xpay_origen=xpay.IN_APP
    )
    assert decode_merchant_parameters(request.merchant_parameters)['DS_XPAYTYPE'] == 'Google'


@pytest.mark.parametrize(
    'fields',
    [
        {'xpay_data': 'abc', 'xpay_decoded_data': DECODED, 'xpay_type': 'Google', 'xpay_origen': 'WEB'},
        {'xpay_data': 'abc'},
        {'xpay_data': 'abc', 'xpay_type': 'Google'},
        {'xpay_type': 'Google', 'xpay_origen': 'WEB'},
        {'xpay_data': 'abc', 'xpay_type': 'Samsung', 'xpay_origen': 'WEB'},
        {'xpay_data': 'abc', 'xpay_type': 'Google', 'xpay_origen': 'web'},
        {'xpay_data': 'a' * 10001, 'xpay_type': 'Google', 'xpay_origen': 'WEB'},
    ],
)
def test_wallet_validation(fields):
    with pytest.raises(ValidationError):
        DirectPaymentMessage(**BASE, **fields)


def test_wallet_fields_stay_off_the_redirect():
    with pytest.raises(ValidationError, match='unknown field'):
        RedirectPaymentMessage(**BASE, DS_XPAYDATA='abc')


def test_xpay_constants():
    assert xpay.TYPES == ('Google', 'Apple')
    assert xpay.ORIGINS == ('WEB', 'InApp')
    assert xpay.PAYMENT_METHODS == ('CARD', 'TOKENIZED_CARD')
