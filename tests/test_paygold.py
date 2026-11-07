import os
import sys
import warnings
from decimal import Decimal

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import pay_methods, paygold, transactions
from redsys.clients import DirectClient
from redsys.models import DirectPaymentMessage, DirectPreauthorizationMessage, decode_merchant_parameters

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
OPERATION = dict(order='000000001', amount=Decimal('10.00'))
SMS = f'{paygold.SMS_MERCHANT}: {paygold.SMS_AMOUNT} {paygold.SMS_CURRENCY} {paygold.SMS_URL}'


def _client():
    return DirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)


def _params(request):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        return decode_merchant_parameters(request.merchant_parameters)


def _message(**fields):
    return DirectPaymentMessage(merchant_code='999008881', terminal=1, **OPERATION, **fields)


def test_pay_gold_link_parameters():
    params = _params(
        _client().pay_gold(
            **OPERATION,
            customer_mobile='666555444',
            customer_mail='buyer@example.com',
            customer_sms_text=SMS,
            p2f_expiry_date=60,
            p2f_xml_data=f'<{paygold.XML_BUYER_NAME}>Ana</{paygold.XML_BUYER_NAME}>',
            pay_methods=pay_methods.CARD + pay_methods.BIZUM,
            merchant_url='https://example.com/notify',
        )
    )
    assert params['Ds_Merchant_TransactionType'] == 15
    assert params['Ds_Merchant_Customer_Mobile'] == '666555444'
    assert params['Ds_Merchant_Customer_Mail'] == 'buyer@example.com'
    assert params['Ds_Merchant_Customer_Sms_Text'] == SMS
    assert params['Ds_Merchant_P2f_ExpiryDate'] == '60'
    assert params['Ds_Merchant_P2f_XmlData'] == '<nombreComprador>Ana</nombreComprador>'
    assert params['Ds_Merchant_PayMethods'] == 'Cz'
    assert params['Ds_Merchant_MerchantURL'] == 'https://example.com/notify'


def test_pay_gold_refund_link():
    params = _params(_client().pay_gold(**OPERATION, alt_transaction_type=transactions.REFUND_WITHOUT_ORIGINAL))
    assert params['Ds_Merchant_AltTransType'] == 34


def test_expiry_change_takes_a_timestamp():
    params = _params(_client().pay_gold_expiry_change(**OPERATION, p2f_expiry_date='2026-11-30-23.59.59.000'))
    assert params['Ds_Merchant_TransactionType'] == 51
    assert params['Ds_Merchant_P2f_ExpiryDate'] == '2026-11-30-23.59.59.000'


@pytest.mark.parametrize(
    'fields',
    [
        {'customer_mobile': '1' * 20},
        {'customer_mail': 'a' * 101},
        {'customer_sms_text': 'Pay now'},
        {'customer_sms_text': paygold.SMS_URL + 'a' * 156},
        {'p2f_expiry_date': '2026-11-30 23:59'},
        {'p2f_expiry_date': '-5'},
        {'p2f_expiry_date': True},
        {'p2f_xml_data': 'a' * 1001},
        {'alt_transaction_type': 3},
    ],
)
def test_paygold_validation(fields):
    with pytest.raises(ValidationError):
        _message(**fields)


def test_paygold_fields_stay_off_the_preauthorization():
    with pytest.raises(ValidationError, match='unknown field'):
        DirectPreauthorizationMessage(merchant_code='999008881', terminal=1, **OPERATION, customer_mobile='666555444')


def test_paygold_constants():
    assert paygold.SMS_PLACEHOLDERS == ('@COMERCIO@', '@IMPORTE@', '@MONEDA@', '@URL@')
    assert paygold.XML_TAGS == ('nombreComprador', 'direccionComprador', 'textoLibre1', 'subjectMailCliente')
