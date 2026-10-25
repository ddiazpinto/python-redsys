import os
import sys
from base64 import b64decode, b64encode
from decimal import Decimal
from json import dumps, loads

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import sca
from redsys.clients import (
    DEFAULT_SIGNATURE_VERSION,
    MERCHANT_PARAMETERS,
    SIGNATURE_VERSION,
    RedirectClient,
)
from redsys.exceptions import UnknownParameterWarning
from redsys.models import (
    CancellationMessage,
    ConfirmationMessage,
    DirectPaymentMessage,
    DirectPreauthorizationMessage,
    RedirectPaymentMessage,
    RefundMessage,
    Response,
)

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'


def _valid(**overrides):
    params = dict(
        merchant_code='999008881',
        terminal=1,
        transaction_type=0,
        currency=978,
        order='000000001',
        amount=Decimal('10.56'),
    )
    params.update(overrides)
    return RedirectPaymentMessage(**params)


def _op(cls, **overrides):
    params = dict(merchant_code='999008881', terminal=1, currency=978, order='000000001', amount=Decimal('5.00'))
    params.update(overrides)
    return cls(**params)


def test_construct_and_serialize_to_wire_names():
    params = _valid(merchant_url='https://example.com/notify').prepare_parameters()
    assert params['Ds_Merchant_MerchantCode'] == '999008881'
    assert params['Ds_Merchant_Order'] == '000000001'
    assert params['Ds_Merchant_Currency'] == 978
    assert params['Ds_Merchant_MerchantURL'] == 'https://example.com/notify'


def test_amount_is_decimal_serialized_to_cents_no_float_drift():
    # The classic float trap: 10.56 * 100 == 1055.999... -> must be exactly 1056.
    assert _valid(amount=Decimal('10.56')).prepare_parameters()['Ds_Merchant_Amount'] == 1056
    assert RedirectPaymentMessage.model_fields['amount'].annotation is Decimal


def test_encode_round_trips_to_base64_json():
    decoded = loads(b64decode(_valid().encode()).decode('utf-8'))
    assert decoded['Ds_Merchant_Amount'] == 1056
    assert decoded['Ds_Merchant_TransactionType'] == 0


def test_optional_fields_excluded_when_unset():
    assert 'Ds_Merchant_UrlOK' not in _valid().prepare_parameters()


def test_order_accepts_up_to_12_characters():
    assert _valid(order='1234abcd5678').prepare_parameters()['Ds_Merchant_Order'] == '1234abcd5678'


def test_validation_rejects_order_longer_than_12_characters():
    with pytest.raises(ValidationError):
        _valid(order='1234abcd56789')


def test_bizum_fields_serialized():
    params = _valid(pay_methods='z', bizum_mobile_number='+34700000000').prepare_parameters()
    assert params['Ds_Merchant_PayMethods'] == 'z'
    assert params['Ds_Merchant_Bizum_MobileNumber'] == '+34700000000'


def test_validation_rejects_bad_order_pattern():
    with pytest.raises(ValidationError):
        _valid(order='bad')


def test_validation_rejects_unknown_snake_case_field():
    # A typo must fail, not be dropped from the signed message.
    with pytest.raises(ValidationError, match='unknown field'):
        _valid(merchant_ulr='https://example.com/notify')


def test_validation_names_the_2x_replacement_for_1x_fields():
    with pytest.raises(ValidationError, match='pay_methods'):
        _valid(payment_method='z')
    with pytest.raises(ValidationError, match='no 2.x equivalent'):
        _valid(transaction_date='2026-10-25')


def test_unmodeled_wire_name_passes_through_with_a_warning():
    # RedSys adds parameters; the wire name is the escape hatch until the library models them.
    with pytest.warns(UnknownParameterWarning):
        params = _valid(Ds_Merchant_Tax_Reference='ABC123').prepare_parameters()
    assert params['Ds_Merchant_Tax_Reference'] == 'ABC123'


def test_validation_rejects_unknown_currency():
    with pytest.raises(ValidationError):
        _valid(currency=111)


def test_validation_rejects_terminal_out_of_range():
    with pytest.raises(ValidationError):
        _valid(terminal=1000)


def test_operation_transaction_type_defaults():
    assert _op(DirectPaymentMessage).prepare_parameters()['Ds_Merchant_TransactionType'] == 0
    assert _op(DirectPreauthorizationMessage).prepare_parameters()['Ds_Merchant_TransactionType'] == 1
    assert _op(ConfirmationMessage).prepare_parameters()['Ds_Merchant_TransactionType'] == 2
    assert _op(RefundMessage).prepare_parameters()['Ds_Merchant_TransactionType'] == 3
    assert _op(CancellationMessage).prepare_parameters()['Ds_Merchant_TransactionType'] == 9


def test_direct_payment_card_fields_serialized():
    params = _op(DirectPaymentMessage, pan='4548810000000003', expiry_date='4912', cvv2='123').prepare_parameters()
    assert params['Ds_Merchant_Pan'] == '4548810000000003'
    assert params['Ds_Merchant_ExpiryDate'] == '4912'
    assert params['Ds_Merchant_Cvv2'] == '123'


def _response(**fields):
    return Response.from_merchant_parameters(b64encode(dumps(fields).encode('utf-8')))


def test_response_predicates_and_code():
    paid = _response(Ds_Response='0000', Ds_Order='000000001', Ds_Amount='1056')
    assert paid.is_paid() and paid.is_authorized()
    assert paid.response_code == 0
    assert paid.amount == Decimal('10.56') and paid.order == '000000001'

    refunded = _response(Ds_Response='0900', Ds_Order='1', Ds_Amount='500')
    assert refunded.is_refunded() and refunded.amount == Decimal('5.00')
    assert refunded.response_code == 900

    declined = _response(Ds_Response='0190', Ds_Order='1', Ds_Amount='100')
    assert not declined.is_paid()
    assert declined.response_code == 190


def test_response_keeps_unmapped_fields():
    resp = _response(Ds_Response='0000', Ds_Order='1', Ds_Amount='100', Ds_Control_1790968949956='1790968949956')
    assert resp.is_paid()
    assert resp.model_extra == {'Ds_Control_1790968949956': '1790968949956'}


def test_response_amount_euro_and_processed_pay_method():
    resp = _response(
        Ds_Response='0000',
        Ds_Order='1',
        Ds_Amount='1000',
        Ds_Currency=840,
        Ds_Amount_Euro='921',
        Ds_ProcessedPayMethod='68',
    )
    assert resp.amount_euro == '921'
    assert resp.processed_pay_method == '68'
    assert resp.model_extra == {}


def test_client_signs_a_request():
    client = RedirectClient(SECRET, merchant_code='999008881', terminal=1, sandbox=True)
    body = client.payment(order='000000001', currency=978, amount=Decimal('10.56')).to_dict()
    assert body[SIGNATURE_VERSION] == DEFAULT_SIGNATURE_VERSION
    assert body[MERCHANT_PARAMETERS]


def test_request_amount_scaled_by_currency_exponent():
    # EUR has 2 decimals -> x100.
    assert _valid(currency=978, amount=Decimal('10.56')).prepare_parameters()['Ds_Merchant_Amount'] == 1056
    # JPY and CLP have 0 decimals -> x1 (the unit is already the smallest).
    assert _valid(currency=392, amount=Decimal('1000')).prepare_parameters()['Ds_Merchant_Amount'] == 1000
    assert _valid(currency=152, amount=Decimal('1500')).prepare_parameters()['Ds_Merchant_Amount'] == 1500


def test_response_amount_scaled_by_currency_exponent():
    assert _response(Ds_Response='0000', Ds_Order='1', Ds_Amount='1056', Ds_Currency='978').amount == Decimal('10.56')
    assert _response(Ds_Response='0000', Ds_Order='1', Ds_Amount='1000', Ds_Currency='392').amount == Decimal('1000')
    # The currency's decimals are kept, as RedSys shows them: 100 EUR minor units are 1.00.
    assert str(_response(Ds_Response='0000', Ds_Order='1', Ds_Amount='100', Ds_Currency='978').amount) == '1.00'
    assert str(_response(Ds_Response='0000', Ds_Order='1', Ds_Amount='100', Ds_Currency='392').amount) == '100'


def test_response_is_canceled():
    canceled = _response(Ds_Response='0400', Ds_Order='1', Ds_Amount='100')
    assert canceled.is_canceled() and canceled.is_authorized()
    assert not canceled.is_paid()


def test_idoper_is_a_direct_card_source():
    # inSite has no dedicated message: once the JS yields an idoper, a direct
    # payment carries it as the card source.
    params = _op(DirectPaymentMessage, idoper='abc123token').prepare_parameters()
    assert params['Ds_Merchant_Idoper'] == 'abc123token'


def test_tokenization_and_cof_fields_serialized():
    from redsys import cof
    from redsys.models import DirectPaymentMessage

    # First payment (cardholder present): ask RedSys to store the card as a token.
    create = DirectPaymentMessage(
        merchant_code='999008881',
        terminal=1,
        currency=978,
        order='000000001',
        amount=Decimal('10.56'),
        pan='4548810000000003',
        expiry_date='4912',
        cvv2='123',
        identifier=cof.REQUEST_TOKEN,
        cof_ini=cof.INITIAL,
        cof_type=cof.RECURRING,
    ).prepare_parameters()
    assert create['Ds_Merchant_Identifier'] == 'REQUIRED'
    assert create['Ds_Merchant_Cof_Ini'] == 'S'
    assert create['Ds_Merchant_Cof_Type'] == 'R'

    # Subsequent merchant-initiated charge using the stored token (no card data).
    charge = DirectPaymentMessage(
        merchant_code='999008881',
        terminal=1,
        currency=978,
        order='000000002',
        amount=Decimal('10.56'),
        identifier='TOKEN-123',
        cof_ini=cof.SUBSEQUENT,
        cof_type=cof.RECURRING,
        cof_txnid='987654321012345',
    ).prepare_parameters()
    assert charge['Ds_Merchant_Identifier'] == 'TOKEN-123'
    assert charge['Ds_Merchant_Cof_Ini'] == 'N'
    assert charge['Ds_Merchant_Cof_Txnid'] == '987654321012345'


def test_recurring_sum_total_scaled_like_amount():
    from redsys.models import DirectPaymentMessage

    params = DirectPaymentMessage(
        merchant_code='999008881',
        terminal=1,
        currency=978,
        order='000000001',
        amount=Decimal('10.00'),
        sum_total=Decimal('120.00'),
        date_frequency='30',
    ).prepare_parameters()
    assert params['Ds_Merchant_SumTotal'] == 12000  # 120.00 EUR -> minor units
    assert params['Ds_Merchant_DateFrecuency'] == '30'


def test_response_captures_token_and_cof_txnid():
    token = _response(
        Ds_Response='0000',
        Ds_Order='1',
        Ds_Amount='1056',
        Ds_Merchant_Identifier='TOKEN-XYZ',
        Ds_Merchant_Cof_Txnid='123456789012345',
    )
    assert token.identifier == 'TOKEN-XYZ'
    assert token.cof_txnid == '123456789012345'


def test_excep_sca_serialized_on_redirect_and_direct():
    assert _valid(excep_sca=sca.MIT).prepare_parameters()['Ds_Merchant_Excep_SCA'] == 'MIT'
    assert _op(DirectPaymentMessage, excep_sca=sca.QUERY).prepare_parameters()['Ds_Merchant_Excep_SCA'] == 'Y'


def test_validation_rejects_merchant_url_longer_than_250():
    with pytest.raises(ValidationError):
        _valid(merchant_url='https://example.com/' + 'a' * 231)


def test_validation_rejects_merchant_data_longer_than_1024():
    with pytest.raises(ValidationError):
        _valid(merchant_data='x' * 1025)


def test_response_language_and_excep_sca():
    resp = _response(Ds_Response='0000', Ds_Order='1', Ds_Language='1', Ds_Excep_SCA='LWV;TRA[30.0]', Ds_Card_PSD2='Y')
    assert resp.language == '1'
    assert resp.excep_sca == 'LWV;TRA[30.0]'
    assert resp.model_extra == {}


def test_response_decodes_unpadded_base64url_parameters():
    from base64 import urlsafe_b64encode

    wire = dumps({'Ds_Response': '0000', 'Ds_Order': '1', 'Ds_Amount': '100'}).encode('utf-8')
    raw = urlsafe_b64encode(wire).rstrip(b'=')
    resp = Response.from_merchant_parameters(raw)
    assert resp.is_paid() and resp.amount == Decimal('1.00')


def test_response_fields_seen_live_and_dcc():
    resp = _response(
        Ds_Response='0195',
        Ds_Order='1',
        Ds_Card_Typology='CONSUMO',
        Ds_ECI='05',
        Ds_Response_Description='REQUIERE AUTENTICACION SCA',
        Ds_Currency_DCC='840',
        Ds_Amount_DCC='117',
    )
    assert (resp.card_typology, resp.eci, resp.response_description) == ('CONSUMO', '05', 'REQUIERE AUTENTICACION SCA')
    assert (resp.currency_dcc, resp.amount_dcc) == ('840', '117')
    assert resp.model_extra == {}


def test_response_bizum_fields():
    resp = _response(
        Ds_Response='0000',
        Ds_Order='1',
        Ds_ProcessedPayMethod='68',
        Ds_Bizum_IdOper='9382755',
        Ds_Bizum_CuentaTruncada='XXXX4000',
    )
    assert (resp.processed_pay_method, resp.bizum_id_oper, resp.bizum_cuenta_truncada) == ('68', '9382755', 'XXXX4000')
    assert resp.model_extra == {}


def test_response_card_number_from_redirect_and_rest_names():
    # Redirect notifications send Ds_Card_Number (seen live 2026-10-25); REST responses send Ds_CardNumber.
    redirect = _response(Ds_Response='0000', Ds_Order='1', Ds_Card_Number='454881******0003')
    rest = _response(Ds_Response='0000', Ds_Order='1', Ds_CardNumber='454881******0003')
    assert redirect.card_number == rest.card_number == '454881******0003'
    assert redirect.model_extra == {}


def test_response_dcc_object():
    resp = _response(Ds_Order='1', Ds_DCC={'InfoMonedaTarjeta': {'monedaDCC': '840'}})
    assert resp.dcc == {'InfoMonedaTarjeta': {'monedaDCC': '840'}}
    assert resp.model_extra == {}


def test_redirect_accepts_stored_credential_fields():
    params = _valid(identifier='REQUIRED', cof_ini='S', cof_type='R', direct_payment='true').prepare_parameters()
    assert params['Ds_Merchant_Identifier'] == 'REQUIRED'
    assert (params['Ds_Merchant_Cof_Ini'], params['Ds_Merchant_Cof_Type']) == ('S', 'R')
    assert params['Ds_Merchant_DirectPayment'] == 'true'
