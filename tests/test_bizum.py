import os
import sys
import warnings
from base64 import b64encode
from decimal import Decimal
from json import dumps

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import bizum, cof, environments, pay_methods
from redsys.clients import DirectClient, RedirectClient
from redsys.codes import describe
from redsys.models import DirectPaymentMessage, RedirectPaymentMessage, Response, decode_merchant_parameters

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
OPERATION = dict(order='000000001', amount=Decimal('1.00'), pay_methods=pay_methods.BIZUM)
ACCOUNT = dict(merchant_code='999008881', terminal=1, sandbox=True)


def _params(request):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        return decode_merchant_parameters(request.merchant_parameters)


@pytest.mark.parametrize('client_class', [RedirectClient, DirectClient])
def test_mit_amount_variation_on_the_tid_generation(client_class):
    request = client_class(SECRET, **ACCOUNT).payment(
        **OPERATION, cof_ini=cof.INITIAL, cof_type=cof.RECURRING, bizum_mrt_amount_variation='200'
    )
    assert _params(request)['Ds_Merchant_Bizum_MrtAmountVariation'] == '200'


def test_redirect_backup_by_operation_id():
    request = RedirectClient(SECRET, **ACCOUNT).payment(
        **OPERATION, bizum_id_oper='12345678901234567890123456789012345'
    )
    assert _params(request)['Ds_Merchant_Bizum_IdOper'] == '12345678901234567890123456789012345'


def test_rest_request_to_pay_and_backup_validation():
    client = DirectClient(SECRET, **ACCOUNT)
    pay = client.payment(
        **OPERATION, bizum_mobile_number='+34700000000', endpoint=client.url(environments.RTP_TRATA_PATH)
    )
    assert _params(pay)['Ds_Merchant_Bizum_MobileNumber'] == '+34700000000'
    validate = client.payment(
        **OPERATION,
        bizum_mobile_number='+34700000000',
        otp=1234,
        endpoint=client.url(environments.RTP_BACKUP_VALIDATION_PATH),
    )
    assert _params(validate)['Ds_Merchant_Otp'] == '1234'
    assert validate.endpoint.endswith('/sis/rest/RTP/validarRespaldoUsuarioRTP')


@pytest.mark.parametrize(
    'model, fields',
    [
        (DirectPaymentMessage, {'bizum_mrt_amount_variation': '2.00'}),
        (DirectPaymentMessage, {'otp': '12a4'}),
        (DirectPaymentMessage, {'otp': True}),
        (DirectPaymentMessage, {'bizum_id_oper': '1'}),
        (RedirectPaymentMessage, {'otp': '1234'}),
    ],
)
def test_bizum_validation(model, fields):
    with pytest.raises(ValidationError):
        model(merchant_code='999008881', terminal=1, order='000000001', amount=Decimal('1.00'), **fields)


def _response(**fields):
    return Response.from_merchant_parameters(b64encode(dumps(fields).encode('utf-8')))


def test_response_rtp_fields():
    response = _response(
        Ds_Response='9998',
        Ds_Order='1',
        Ds_RtpStatus=bizum.RTP_KO,
        Ds_RtpResponse=bizum.BACKUP_AVAILABLE,
        Ds_RtpDescription='SIS-T backup',
        Ds_RtpBackupHtml='PGh0bWw+',
        Ds_RtpBackupTemplate='e30=',
    )
    assert (response.rtp_status, response.rtp_response) == ('KO', 'BIZ00233')
    assert (response.rtp_description, response.rtp_backup_html, response.rtp_backup_template) == (
        'SIS-T backup',
        'PGh0bWw+',
        'e30=',
    )
    assert response.model_extra == {}


def test_bizum_constants_are_described():
    assert bizum.RTP_STATUSES == ('OK', 'KO')
    assert len(set(bizum.RTP_RESPONSES)) == 14
    for code in bizum.RTP_RESPONSES:
        assert describe(code, 'en'), code
    assert bizum.PAYER_NOT_FOUND == 'BIZ00009'
