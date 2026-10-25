"""Live tests against the RedSys test environment with RedSys's public test merchant.

Opt-in: they run only with REDSYS_LIVE=1 and need network access and the http extra.
The merchant, terminal, secret and card are the ones RedSys publishes for integration
tests; no money moves.
"""

import os
import random
import re
import time
from decimal import Decimal

import pytest

pytestmark = pytest.mark.skipif(os.environ.get('REDSYS_LIVE') != '1', reason='set REDSYS_LIVE=1 to run')
httpx = pytest.importorskip('httpx')

from redsys import cof, currencies, sca, threeds  # noqa: E402
from redsys.clients import HMAC_SHA256_V1, HMAC_SHA512_V1, HMAC_SHA512_V2, DirectClient  # noqa: E402

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
MERCHANT_CODE = '999008881'
CARD = {'pan': '4548810000000003', 'expiry_date': '4912', 'cvv2': '123'}  # always challenges
BROWSER = threeds.browser_info(
    accept_header='text/html',
    user_agent='python-redsys live tests',
    language='es-ES',
    color_depth=24,
    screen_height=1080,
    screen_width=1920,
    tz=-60,
)
VERSIONS = [HMAC_SHA512_V2, HMAC_SHA512_V1, HMAC_SHA256_V1]


def _client(version):
    return DirectClient(SECRET, merchant_code=MERCHANT_CODE, terminal=1, sandbox=True, signature_version=version)


def _operation():
    order = f'{int(time.time() * 1000) % 10**10:010d}{random.randint(0, 99):02d}'
    return {'order': order, 'amount': Decimal('1.00'), 'currency': currencies.EUR}


def _hidden(page, name):
    return re.search(rf'name="{name}"\s+value="([^"]*)"', page).group(1)


def _answer_simulated_challenge(response):
    """Do what the cardholder's browser does on RedSys's simulator ACS (sis-d); return the cres."""
    page = httpx.post(response.acs_url, data={'creq': response.creq}, timeout=30).text
    action = re.search(r'name="rreqform" action="([^"]+)"', page).group(1)
    httpx.post(action, data={'RREQ': _hidden(page, 'RREQ')}, timeout=30).raise_for_status()
    return _hidden(page, 'cres')


@pytest.mark.parametrize('version', VERSIONS)
def test_live_inicia_returns_the_card_3ds_configuration(version):
    response = _client(version).inicia(emv3ds=threeds.card_data(), **_operation(), **CARD).send()
    assert response.protocol_version.startswith('2.')
    assert response.three_ds_server_trans_id


@pytest.mark.parametrize('version', VERSIONS)
def test_live_payment_without_authentication_requires_sca(version):
    response = _client(version).payment(direct_payment='true', **_operation(), **CARD).send()
    assert response.response_code == 195


def _challenged_payment(client, operation, **fields):
    """Initialization, authentication with the simulator's challenge, and the final authorization."""
    card_config = client.inicia(emv3ds=threeds.card_data(), **operation, **CARD).send()
    authentication = threeds.authentication_data(
        three_ds_server_trans_id=card_config.three_ds_server_trans_id,
        notification_url='https://example.com/3ds',
        protocol_version=card_config.protocol_version,
        browser=BROWSER,
        three_ds_comp_ind='N',
    )
    challenge = client.payment(emv3ds=authentication, **operation, **CARD, **fields).send()
    assert challenge.requires_challenge()

    cres = _answer_simulated_challenge(challenge)
    final = threeds.challenge_response(cres=cres, protocol_version=challenge.protocol_version)
    return client.payment(emv3ds=final, **operation, **CARD, **fields).send()


@pytest.mark.parametrize('version', VERSIONS)
def test_live_challenged_payment_then_refund(version):
    client, operation = _client(version), _operation()
    payment = _challenged_payment(client, operation)
    assert payment.is_paid() and payment.authorization_code

    refund = client.refund(**operation).send()
    assert refund.is_refunded()


@pytest.mark.parametrize('version', VERSIONS)
def test_live_token_then_merchant_initiated_charge(version):
    client = _client(version)
    first = _challenged_payment(
        client, _operation(), identifier=cof.REQUEST_TOKEN, cof_ini=cof.INITIAL, cof_type=cof.RECURRING
    )
    assert first.is_paid() and first.identifier and first.cof_txnid

    charge = client.payment(
        identifier=first.identifier,
        cof_ini=cof.SUBSEQUENT,
        cof_type=cof.RECURRING,
        cof_txnid=first.cof_txnid,
        excep_sca=sca.MIT,
        direct_payment='true',
        **_operation(),
    ).send()
    assert charge.is_paid()
