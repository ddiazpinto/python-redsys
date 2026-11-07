import os
import sys
from decimal import Decimal
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import environments
from redsys.clients import DirectClient, RedirectClient
from redsys.exceptions import ValidationError

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
MERCHANT_CODE = '999008881'
ORDER = '000000001'
HOSTS = {
    'DESA': 'https://sis-d.redsys.es',
    'INTE': 'https://sis-i.redsys.es:25443',
    'TEST': 'https://sis-t.redsys.es:25443',
    'PROD': 'https://sis.redsys.es',
}


def _payment(client):
    return client.payment(order=ORDER, currency=978, amount=Decimal('10.56'))


# == Environments ==


@pytest.mark.parametrize('environment', HOSTS)
def test_each_environment_resolves_its_endpoints(environment):
    host = HOSTS[environment]
    assert RedirectClient(SECRET, environment=environment).endpoint == f'{host}/sis/realizarPago'
    direct = DirectClient(SECRET, environment=environment)
    assert direct.endpoint == f'{host}/sis/rest/trataPeticionREST'
    assert direct.inicia_endpoint == f'{host}/sis/rest/iniciaPeticionREST'


def test_environment_constants_name_the_hosts():
    assert environments.HOSTS == HOSTS


@pytest.mark.parametrize(
    'options, environment, sandbox',
    [
        ({}, 'PROD', False),
        ({'sandbox': False}, 'PROD', False),
        ({'sandbox': True}, 'TEST', True),
        ({'environment': 'TEST', 'sandbox': True}, 'TEST', True),
        ({'environment': 'PROD', 'sandbox': False}, 'PROD', False),
        ({'environment': 'INTE'}, 'INTE', True),
    ],
)
def test_sandbox_maps_to_an_environment(options, environment, sandbox):
    client = RedirectClient(SECRET, **options)
    assert client.environment == environment
    assert client.sandbox is sandbox


@pytest.mark.parametrize(
    'options',
    [
        {'environment': 'PROD', 'sandbox': True},
        {'environment': 'TEST', 'sandbox': False},
        {'environment': 'DESA', 'sandbox': True},
        {'environment': 'INTE', 'sandbox': False},
    ],
)
def test_contradictory_environment_and_sandbox_raise(options):
    with pytest.raises(ValidationError):
        RedirectClient(SECRET, **options)


def test_unknown_environment_raises():
    with pytest.raises(ValidationError):
        RedirectClient(SECRET, environment='STAGING')


def test_class_constants_stay_readable():
    assert RedirectClient.REAL_ENDPOINT == 'https://sis.redsys.es/sis/realizarPago'
    assert RedirectClient.TEST_ENDPOINT == 'https://sis-t.redsys.es:25443/sis/realizarPago'
    assert DirectClient.REAL_ENDPOINT == 'https://sis.redsys.es/sis/rest/trataPeticionREST'
    assert DirectClient.TEST_ENDPOINT == 'https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST'
    assert DirectClient.INICIA_REAL_ENDPOINT == 'https://sis.redsys.es/sis/rest/iniciaPeticionREST'
    assert DirectClient.INICIA_TEST_ENDPOINT == 'https://sis-t.redsys.es:25443/sis/rest/iniciaPeticionREST'


# == Request endpoint ==


def test_redirect_request_carries_its_endpoint():
    client = RedirectClient(SECRET, merchant_code=MERCHANT_CODE, terminal=1, environment='INTE')
    assert _payment(client).endpoint == 'https://sis-i.redsys.es:25443/sis/realizarPago'


def test_direct_request_carries_its_endpoint():
    client = DirectClient(SECRET, merchant_code=MERCHANT_CODE, terminal=1, sandbox=True)
    assert _payment(client).endpoint == client.endpoint
    assert client.inicia(order=ORDER, currency=978, amount=Decimal('10.56')).endpoint == client.inicia_endpoint


def test_send_posts_to_the_request_endpoint():
    pytest.importorskip('httpx')
    client = DirectClient(SECRET, merchant_code=MERCHANT_CODE, terminal=1, environment='DESA')
    request = _payment(client)
    with mock.patch('httpx.post') as post, mock.patch.object(client, 'parse_response'):
        request.send()
    assert post.call_args.args == ('https://sis-d.redsys.es/sis/rest/trataPeticionREST',)
