import os
import sys
import warnings
from base64 import b64encode
from decimal import Decimal
from json import dumps

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import options
from redsys.clients import DirectClient, RedirectClient
from redsys.models import (
    CancellationMessage,
    ConfirmationMessage,
    DirectPaymentMessage,
    DirectPreauthorizationMessage,
    RedirectPaymentMessage,
    RedirectPreauthorizationMessage,
    RefundMessage,
    Response,
    decode_merchant_parameters,
)

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
BASE = dict(merchant_code='999008881', terminal=1, order='000000001', amount=Decimal('1.00'))
REDIRECT = [RedirectPaymentMessage, RedirectPreauthorizationMessage]
DIRECT = [DirectPaymentMessage, DirectPreauthorizationMessage]
OPERATIONS = [ConfirmationMessage, RefundMessage, CancellationMessage]


def _params(model, **fields):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        return model(**BASE, **fields).prepare_parameters()


def _rejects(model, **fields):
    with pytest.raises(ValidationError):
        model(**BASE, **fields)


# == Fields and the models that take them ==

CASES = [
    ('group', '123456789', 'Ds_Merchant_Group', REDIRECT + DIRECT),
    ('email_titular', 'cardholder@example.com', 'Ds_Merchant_Email_Titular', REDIRECT + DIRECT),
    ('merchant_descriptor', 'EXAMPLE*SHOP', 'Ds_Merchant_MerchantDescriptor', REDIRECT + DIRECT + OPERATIONS),
    ('client_ip', '192.168.100.200', 'Ds_Merchant_ClientIP', DIRECT + OPERATIONS),
    (
        'tax_reference',
        '90521234567890123456',
        'Ds_Merchant_Tax_Reference',
        [RedirectPaymentMessage, DirectPaymentMessage],
    ),
    ('ota', options.OTA_INITIAL, 'Ds_Merchant_OTA', [RedirectPaymentMessage, DirectPaymentMessage]),
    ('financing', options.FINANCING_QUERY, 'Ds_Merchant_Financing', [DirectPaymentMessage]),
    ('financing', {'plazos': '3'}, 'Ds_Merchant_Financing', [DirectPaymentMessage]),
    ('mpi_external', {'Eci': '05', 'protocolVersion': '2.2.0'}, 'Ds_Merchant_MpiExternal', DIRECT),
    ('token_data', {'tokenCryptogram': 'abc'}, 'Ds_Merchant_TokenData', DIRECT),
    ('shipping_address_pyp', options.SHIPPING_ADDRESS, 'Ds_Merchant_ShippingAddressPyP', REDIRECT),
    ('perso_code', 3, 'Ds_Merchant_PersoCode', REDIRECT),
    ('transaction_date', '2026-10-25', 'Ds_Merchant_TransactionDate', [RefundMessage]),
    ('rts', '123456789012345678901234', 'Ds_Merchant_RTS', [RefundMessage]),
    ('pan', '4548810000000003', 'Ds_Merchant_Pan', REDIRECT + DIRECT),
    ('expiry_date', '4912', 'Ds_Merchant_ExpiryDate', REDIRECT + DIRECT),
    ('cvv2', '123', 'Ds_Merchant_Cvv2', REDIRECT + DIRECT),
    ('idoper', 'a' * 40, 'Ds_Merchant_Idoper', REDIRECT + DIRECT),
    ('emv3ds', {'shipAddrCity': 'Madrid'}, 'Ds_Merchant_EMV3DS', REDIRECT + DIRECT),
]
MODELS = REDIRECT + DIRECT + OPERATIONS


@pytest.mark.parametrize('name, value, wire, models', CASES)
def test_field_serializes_by_its_wire_name_on_the_models_that_take_it(name, value, wire, models):
    for model in models:
        assert _params(model, **{name: value})[wire] == value, model.__name__
        assert _params(model, **{wire: value})[wire] == value, model.__name__


@pytest.mark.parametrize('name, value, wire, models', CASES)
def test_field_is_unknown_on_the_other_models(name, value, wire, models):
    for model in MODELS:
        if model not in models:
            with pytest.raises(ValidationError, match='unknown field'):
                model(**BASE, **{name: value})


def test_matching_data_and_acquirer_identifier():
    params = _params(DirectPaymentMessage, matching_data='A' * 21, acquirer_identifier='123456')
    assert (params['Ds_Merchant_MatchingData'], params['Ds_Acquirer_Identifier']) == ('A' * 21, '123456')
    assert _params(DirectPaymentMessage, Ds_Merchant_MatchingData='X1', Ds_Acquirer_Identifier='1')
    _rejects(DirectPaymentMessage, matching_data='X1')
    _rejects(DirectPaymentMessage, acquirer_identifier='1')


@pytest.mark.parametrize(
    'model, fields',
    [
        (RedirectPaymentMessage, {'group': '1234567890'}),
        (RedirectPaymentMessage, {'group': 'ABC'}),
        (RedirectPaymentMessage, {'email_titular': 'a' * 101}),
        (RedirectPaymentMessage, {'merchant_descriptor': 'a' * 26}),
        (RefundMessage, {'client_ip': '1' * 16}),
        (RedirectPaymentMessage, {'tax_reference': '1' * 101}),
        (RedirectPaymentMessage, {'ota': 'N'}),
        (DirectPaymentMessage, {'financing': 'N'}),
        (DirectPaymentMessage, {'matching_data': 'A' * 22, 'acquirer_identifier': '1'}),
        (DirectPaymentMessage, {'matching_data': 'A', 'acquirer_identifier': '1234567'}),
        (RedirectPaymentMessage, {'shipping_address_pyp': 'Y'}),
        (RedirectPaymentMessage, {'perso_code': 10}),
        (RefundMessage, {'transaction_date': '25/10/2026'}),
        (RefundMessage, {'rts': '1' * 25}),
        (RefundMessage, {'rts': 'abc'}),
        (RedirectPaymentMessage, {'pan': '1234'}),
    ],
)
def test_field_validation(model, fields):
    _rejects(model, **fields)


def test_transaction_date_is_no_longer_a_1x_name():
    assert _params(RefundMessage, transaction_date='2026-10-25')['Ds_Merchant_TransactionDate'] == '2026-10-25'
    with pytest.raises(ValidationError, match='unknown field'):
        RedirectPaymentMessage(**BASE, transaction_date='2026-10-25')


def test_options_constants():
    assert options.SHIPPING_ADDRESS_OPTIONS == ('S', 'N')
    assert (options.OTA_INITIAL, options.FINANCING_QUERY) == ('S', 'Y')


def test_clients_reach_the_new_fields():
    redirect = RedirectClient(SECRET, merchant_code='999008881', terminal=1)
    params = decode_merchant_parameters(
        redirect.payment(order='000000001', amount=Decimal('1.00'), pan='4548810000000003').merchant_parameters
    )
    assert params['Ds_Merchant_Pan'] == '4548810000000003'
    direct = DirectClient(SECRET, merchant_code='999008881', terminal=1)
    request = direct.refund(order='000000001', amount=Decimal('1.00'), transaction_date='2026-10-25', rts='12')
    params = decode_merchant_parameters(request.merchant_parameters)
    assert (params['Ds_Merchant_TransactionDate'], params['Ds_Merchant_RTS']) == ('2026-10-25', '12')


# == Response ==


def _response(**fields):
    return Response.from_merchant_parameters(b64encode(dumps(fields).encode('utf-8')))


def test_response_rts_and_two_phase_url():
    response = _response(
        Ds_Response='0900',
        Ds_Order='1',
        rts='123456789012345678901234',
        Ds_UrlPago2Fases='https://sis-t.redsys.es:25443/sis/p2f?t=abc',
    )
    assert response.rts == '123456789012345678901234'
    assert response.url_pago_2_fases == 'https://sis-t.redsys.es:25443/sis/p2f?t=abc'
    assert response.model_extra == {}
