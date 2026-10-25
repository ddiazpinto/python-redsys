import os
import sys
from base64 import b64decode, b64encode
from decimal import Decimal
from json import dumps, loads

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import threeds
from redsys.clients import DirectClient
from redsys.models import DirectPaymentMessage, Response

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'


def _card_request(emv3ds):
    return DirectPaymentMessage(
        merchant_code='999008881',
        terminal=2,
        currency=978,
        order='000000001',
        amount=Decimal('10.00'),
        pan='4548810000000003',
        expiry_date='4912',
        cvv2='123',
        emv3ds=emv3ds,
    )


def _response(**fields):
    return Response.from_merchant_parameters(b64encode(dumps(fields).encode('utf-8')))


def test_card_data_serialized_inline_as_object():
    params = _card_request(threeds.card_data()).prepare_parameters()
    assert params['Ds_Merchant_EMV3DS'] == {'threeDSInfo': 'CardData'}
    decoded = loads(b64decode(_card_request(threeds.card_data()).encode()).decode('utf-8'))
    assert decoded['Ds_Merchant_EMV3DS'] == {'threeDSInfo': 'CardData'}


def test_authentication_data_builder_and_serialization():
    browser = threeds.browser_info(
        accept_header='text/html',
        user_agent='Mozilla/5.0',
        language='ES-es',
        color_depth=24,
        screen_height=1250,
        screen_width=1320,
        tz=52,
    )
    emv = threeds.authentication_data(
        three_ds_server_trans_id='8de84430-3336-4ff4-b18d-f073b546ccea',
        notification_url='https://example.com/3ds',
        protocol_version='2.1.0',
        browser=browser,
    )
    assert emv['threeDSInfo'] == 'AuthenticationData'
    assert emv['threeDSCompInd'] == 'Y'
    assert emv['browserJavaEnabled'] == 'false' and emv['browserJavascriptEnabled'] == 'true'
    assert emv['browserColorDepth'] == '24' and emv['browserTZ'] == '52'
    params = _card_request(emv).prepare_parameters()
    assert params['Ds_Merchant_EMV3DS']['threeDSServerTransID'] == '8de84430-3336-4ff4-b18d-f073b546ccea'


def test_challenge_response_builder():
    emv = threeds.challenge_response(cres='CRESDATA', protocol_version='2.1.0')
    assert emv == {'threeDSInfo': 'ChallengeResponse', 'protocolVersion': '2.1.0', 'cres': 'CRESDATA'}


def test_inicia_response_card_configuration():
    resp = _response(
        Ds_Order='000000001',
        Ds_MerchantCode='999008881',
        Ds_Terminal='2',
        Ds_TransactionType='0',
        Ds_EMV3DS={
            'protocolVersion': '2.1.0',
            'threeDSServerTransID': '8de84430-3336-4ff4-b18d-f073b546ccea',
            'threeDSInfo': 'CardConfiguration',
            'threeDSMethodURL': 'https://sis.redsys.es/sis-simulador-web/threeDsMethod.jsp',
        },
        Ds_Card_PSD2='Y',
    )
    assert resp.protocol_version == '2.1.0'
    assert resp.three_ds_server_trans_id == '8de84430-3336-4ff4-b18d-f073b546ccea'
    assert resp.three_ds_method_url.endswith('threeDsMethod.jsp')
    assert resp.card_psd2 == 'Y'
    assert not resp.requires_challenge()
    assert not resp.is_no_3ds()
    assert not resp.is_paid()  # no Ds_Response yet


def test_inicia_response_no_3ds():
    resp = _response(Ds_Order='1', Ds_EMV3DS={'protocolVersion': 'NO_3DS_V2'})
    assert resp.is_no_3ds()
    assert not resp.requires_challenge()


def test_auth_response_frictionless_is_paid():
    resp = _response(
        Ds_Amount='1000',
        Ds_Currency='978',
        Ds_Order='000000001',
        Ds_Response='0000',
        Ds_AuthorisationCode='694432',
        Ds_Card_Brand='1',
    )
    assert resp.is_paid()
    assert not resp.requires_challenge()
    assert resp.amount == Decimal('10.00')


def test_auth_response_challenge_required():
    resp = _response(
        Ds_Amount='1000',
        Ds_Currency='978',
        Ds_Order='000000001',
        Ds_EMV3DS={
            'threeDSInfo': 'ChallengeRequest',
            'protocolVersion': '2.1.0',
            'acsURL': 'https://sis.redsys.es/sis-simulador-web/authenticationRequest.jsp',
            'creq': 'eyJ0aHJlZURTU2VydmVy',
        },
    )
    assert resp.requires_challenge()
    assert resp.acs_url.endswith('authenticationRequest.jsp')
    assert resp.creq == 'eyJ0aHJlZURTU2VydmVy'
    assert not resp.is_paid()


def test_response_code_9568_is_an_error_not_a_challenge():
    # SIS0568 / 9568: initialization request rejected (wrong transaction type), per the portal's code table.
    resp = _response(Ds_Order='1', Ds_Response='9568')
    assert resp.response_code == 9568 and not resp.requires_challenge() and not resp.is_authorized()


def test_inicia_posts_to_inicia_endpoint():
    try:
        import httpx
    except ImportError:
        print('skip (httpx not installed)')
        return
    from redsys.clients import MERCHANT_PARAMETERS, SIGNATURE, SIGNATURE_VERSION
    from redsys.crypto import HMAC_SHA512_V1, get_signer

    # A valid signed inicia-style response to round-trip through parse_response.
    params = b64encode(
        dumps(
            {
                'Ds_Order': '000000001',
                'Ds_EMV3DS': {'protocolVersion': '2.1.0', 'threeDSInfo': 'CardConfiguration'},
            }
        ).encode('utf-8')
    )
    signature = get_signer(SECRET, HMAC_SHA512_V1).sign('000000001', params)
    payload = {
        SIGNATURE_VERSION: HMAC_SHA512_V1,
        MERCHANT_PARAMETERS: params.decode('utf-8'),
        SIGNATURE: signature.decode('utf-8'),
    }

    captured = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    def _fake_post(url, json=None, **kwargs):
        captured['url'] = url
        return _FakeResponse()

    original_post = httpx.post
    httpx.post = _fake_post
    try:
        response = (
            DirectClient(SECRET, merchant_code='999008881', terminal=2, sandbox=True)
            .inicia(
                order='000000001',
                currency=978,
                amount=Decimal('10.00'),
                pan='4548810000000003',
                expiry_date='4912',
                cvv2='123',
                emv3ds=threeds.card_data(),
            )
            .send()
        )
    finally:
        httpx.post = original_post

    assert captured['url'] == 'https://sis-t.redsys.es:25443/sis/rest/iniciaPeticionREST'
    assert response.protocol_version == '2.1.0'
