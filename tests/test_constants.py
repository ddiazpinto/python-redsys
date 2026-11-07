import os
import sys
from base64 import b64encode
from json import dumps
from types import ModuleType

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import (
    cards,
    emv3ds,
    languages,
    options,
    processed_pay_methods,
    sca,
    secure_payment,
    threeds,
)
from redsys.models import Response


def _named(module: ModuleType, exclude=()):
    return {
        value
        for name, value in vars(module).items()
        if name.isupper() and not isinstance(value, (tuple, dict)) and name not in exclude
    }


@pytest.mark.parametrize(
    'module, tuples',
    [
        (cards, ('CARD_TYPES', 'BRANDS', 'PSD2_VALUES')),
        (processed_pay_methods, ('PROCESSED_PAY_METHODS',)),
        (secure_payment, ('SECURE_PAYMENTS',)),
        (languages, ('LANGUAGES',)),
    ],
)
def test_each_named_value_is_in_one_tuple(module, tuples):
    collected = [value for name in tuples for value in getattr(module, name)]
    assert len(collected) == len(set(collected))
    assert set(collected) == _named(module)


def test_emv3ds_values():
    assert emv3ds.REQUEST_INFOS == ('CardData', 'AuthenticationData', 'ChallengeResponse', '3RI-Recurring', '3RI-OTA')
    assert emv3ds.RESPONSE_INFOS == ('CardConfiguration', 'ChallengeRequest')
    assert emv3ds.PROTOCOL_VERSIONS == ('1.0.2', '2.1.0', '2.2.0', 'NO_3DS_V2')
    assert emv3ds.METHOD_COMPLETION_INDICATORS == ('Y', 'N', 'U')
    assert emv3ds.CHALLENGE_WINDOW_SIZES == ('01', '02', '03', '04', '05')
    assert emv3ds.CHALLENGE_INDICATORS == ('03', '04')
    assert emv3ds.WHITELIST_STATUSES == ('N', 'E', 'P', 'R', 'U')


def test_card_and_payment_values():
    assert cards.CARD_TYPES == ('C', 'D', 'V', 'X')
    assert cards.BRANDS == ('1', '2', '6', '7', '8', '9', '22')
    assert secure_payment.SECURE_PAYMENTS == ('0', '1', '2')
    assert processed_pay_methods.BIZUM == '68'
    assert len(processed_pay_methods.PROCESSED_PAY_METHODS) == 50


def test_option_values():
    assert options.DIRECT_PAYMENTS == ('true', 'moto')
    assert options.DCC_QUERIES == ('Y', 'N')
    assert sca.QUERIES == ('Y', 'N')
    assert sca.WHITELIST == 'WHL'
    assert sca.WHITELIST not in sca.EXEMPTIONS


def test_languages_follow_the_insite_catalog():
    assert (languages.BULGARIAN, languages.HINDI, languages.KOREAN, languages.ARABIC) == (100, 356, 410, 682)
    assert len(languages.LANGUAGES) == 35


def test_threeds_builders_keep_their_output():
    assert threeds.card_data() == {'threeDSInfo': 'CardData'}
    assert threeds.challenge_response(cres='c', protocol_version='2.2.0')['threeDSInfo'] == 'ChallengeResponse'
    data = threeds.authentication_data(
        three_ds_server_trans_id='id', notification_url='https://example.com', protocol_version='2.2.0', browser={}
    )
    assert (data['threeDSInfo'], data['threeDSCompInd']) == ('AuthenticationData', 'Y')


def _response(**fields):
    return Response.from_merchant_parameters(b64encode(dumps(fields).encode('utf-8')))


def test_response_predicates_read_the_constants():
    assert _response(Ds_EMV3DS={'protocolVersion': emv3ds.NO_3DS_V2}).is_no_3ds()
    assert _response(Ds_EMV3DS={'threeDSInfo': emv3ds.CHALLENGE_REQUEST}).requires_challenge()
    assert not _response(Ds_EMV3DS={'threeDSInfo': emv3ds.CARD_CONFIGURATION}).requires_challenge()
    response = _response(Ds_Card_Brand='1', Ds_Card_Type='C', Ds_SecurePayment='2', Ds_ProcessedPayMethod='68')
    assert response.card_brand == cards.VISA and response.card_type == cards.CREDIT
    assert response.secure_payment == secure_payment.SECURE
    assert response.processed_pay_method == processed_pay_methods.BIZUM
