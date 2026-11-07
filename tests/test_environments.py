import asyncio
import os
import sys
from base64 import urlsafe_b64encode
from decimal import Decimal
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import environments
from redsys.clients import (
    HMAC_SHA256_V1,
    HMAC_SHA512_V1,
    HMAC_SHA512_V2,
    AsyncDirectClient,
    DirectClient,
    RedirectClient,
)
from redsys.exceptions import ValidationError

SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
MERCHANT_CODE = '999008881'
# RedSys's public example key for its test merchant, terminal 001.
PUBLIC_API_KEY = 'TEST_OTk5MDA4ODgxXzAwMV9zcTdIanJVT0JmS21DNTc2SUxnc2tENXNyVTg3MGdKNw'
ORDER = '000000001'
CLIENTS = [RedirectClient, DirectClient, AsyncDirectClient]
HOSTS = {
    'DESA': 'https://sis-d.redsys.es',
    'INTE': 'https://sis-i.redsys.es:25443',
    'TEST': 'https://sis-t.redsys.es:25443',
    'PROD': 'https://sis.redsys.es',
}


def _api_key(prefix='TEST', plain=f'{MERCHANT_CODE}_001_{SECRET}', padded=True):
    payload = urlsafe_b64encode(plain.encode()).decode()
    return f'{prefix}_{payload if padded else payload.rstrip("=")}'


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


RTP_TRATA = 'https://sis-t.redsys.es:25443/sis/rest/RTP/trataPeticionREST'


def _direct(client_class=DirectClient):
    return client_class(SECRET, merchant_code=MERCHANT_CODE, terminal=1, sandbox=True)


def test_url_joins_the_environment_host_and_a_path():
    client = _direct()
    assert client.url(environments.RTP_TRATA_PATH) == RTP_TRATA
    assert RedirectClient(SECRET, environment='DESA').url('/x') == 'https://sis-d.redsys.es/x'


@pytest.mark.parametrize('path', ['sis/rest/x', '', None])
def test_url_requires_an_absolute_path(path):
    with pytest.raises(ValidationError):
        _direct().url(path)


def test_rtp_paths():
    assert environments.RTP_CHECK_PATH == '/sis/rest/RTP/checkRtpUsuario'
    assert environments.RTP_TRATA_PATH == '/sis/rest/RTP/trataPeticionREST'
    assert environments.RTP_BACKUP_PATH == '/sis/rest/RTP/respaldarUsuarioRTP'
    assert environments.RTP_BACKUP_VALIDATION_PATH == '/sis/rest/RTP/validarRespaldoUsuarioRTP'


@pytest.mark.parametrize(
    'client_class, method',
    [
        (RedirectClient, 'payment'),
        (RedirectClient, 'authentication'),
        (DirectClient, 'payment'),
        (DirectClient, 'refund_without_original'),
        (DirectClient, 'inicia'),
        (DirectClient, 'inicia_payment'),
        (AsyncDirectClient, 'refund'),
    ],
)
def test_endpoint_option_replaces_the_request_endpoint_and_is_not_signed(client_class, method):
    client = _direct(client_class)
    request = getattr(client, method)(order=ORDER, amount=Decimal('10.56'), endpoint=RTP_TRATA)
    plain = getattr(client, method)(order=ORDER, amount=Decimal('10.56'))
    assert request.endpoint == RTP_TRATA
    assert request.to_dict() == plain.to_dict()
    assert client.endpoint != RTP_TRATA


def test_endpoint_option_on_request_and_challenge_response():
    client = _direct()
    assert client.request(0, order=ORDER, amount=Decimal('1.00'), endpoint=RTP_TRATA).endpoint == RTP_TRATA
    request = client.challenge_response(
        cres='abc', protocol_version='2.1.0', order=ORDER, amount=Decimal('1.00'), endpoint=RTP_TRATA
    )
    assert request.endpoint == RTP_TRATA


@pytest.mark.parametrize(
    'endpoint',
    ['http://sis-t.redsys.es:25443/sis/rest/RTP/trataPeticionREST', '/sis/rest/RTP/trataPeticionREST', 'https://', 7],
)
def test_endpoint_option_must_be_an_https_url(endpoint):
    with pytest.raises(ValidationError):
        _direct().payment(order=ORDER, amount=Decimal('1.00'), endpoint=endpoint)
    with pytest.raises(ValidationError):
        _direct().inicia(order=ORDER, amount=Decimal('1.00'), endpoint=endpoint)


def test_send_posts_to_the_endpoint_option():
    pytest.importorskip('httpx')
    client = _direct()
    request = client.payment(order=ORDER, amount=Decimal('1.00'), endpoint=client.url(environments.RTP_TRATA_PATH))
    with mock.patch('httpx.post') as post, mock.patch.object(client, 'parse_response'):
        request.send()
    assert post.call_args.args == (RTP_TRATA,)


def test_async_send_posts_to_the_endpoint_option():
    pytest.importorskip('httpx')
    client = _direct(AsyncDirectClient)
    http_client = mock.MagicMock()
    http_client.__aenter__ = mock.AsyncMock(return_value=http_client)
    http_client.__aexit__ = mock.AsyncMock(return_value=None)
    http_client.post = mock.AsyncMock()
    request = client.refund(order=ORDER, amount=Decimal('1.00'), endpoint=RTP_TRATA)
    with mock.patch('httpx.AsyncClient', return_value=http_client), mock.patch.object(client, '_parse_http_response'):
        asyncio.run(request.send())
    assert http_client.post.call_args.args == (RTP_TRATA,)


# == API key ==


@pytest.mark.parametrize('client_class', CLIENTS)
@pytest.mark.parametrize('version', [HMAC_SHA512_V2, HMAC_SHA512_V1, HMAC_SHA256_V1])
def test_api_key_client_signs_like_a_parameter_built_client(client_class, version):
    built = client_class.from_api_key(_api_key(), signature_version=version)
    expected = client_class(SECRET, merchant_code=MERCHANT_CODE, terminal=1, sandbox=True, signature_version=version)
    assert _payment(built).to_dict() == _payment(expected).to_dict()


def test_public_example_api_key():
    client = RedirectClient.from_api_key(PUBLIC_API_KEY)
    assert (client.merchant_code, client.terminal, client.environment) == (MERCHANT_CODE, 1, 'TEST')
    assert client._secret_key == SECRET


def test_api_key_carries_the_account_and_environment():
    client = DirectClient.from_api_key(_api_key('PROD'))
    assert (client.merchant_code, client.terminal, client.environment) == (MERCHANT_CODE, 1, 'PROD')
    assert client.endpoint == 'https://sis.redsys.es/sis/rest/trataPeticionREST'


def test_api_key_accepts_an_unpadded_payload():
    assert _api_key().endswith('=') and not _api_key(padded=False).endswith('=')
    client = RedirectClient.from_api_key(_api_key(padded=False))
    assert (client.merchant_code, client.terminal) == (MERCHANT_CODE, 1)


def test_api_key_splits_only_at_the_first_underscore_and_keeps_the_secret_whole():
    # '???' encodes as 'Pz8_', so the payload itself holds an underscore.
    secret = 'a_b_????'
    key = _api_key(plain=f'{MERCHANT_CODE}_1_{secret}')
    assert '_' in key.partition('_')[2]
    client = RedirectClient.from_api_key(key)
    assert client._secret_key == secret


@pytest.mark.parametrize(
    'api_key',
    [
        '',
        None,
        'TEST',
        'TEST_',
        _api_key('TES'),
        _api_key('TESTS'),
        _api_key('LIVE'),
        _api_key('test'),
        'TEST_not*base64',
        'TEST_a',
        f'TEST_{urlsafe_b64encode(bytes([255, 254, 253])).decode()}',
        _api_key(plain=f'{MERCHANT_CODE}_001'),
        _api_key(plain=f'{MERCHANT_CODE}_001_'),
        _api_key(plain=f'ABC_001_{SECRET}'),
        _api_key(plain=f'{MERCHANT_CODE}_ABC_{SECRET}'),
        _api_key(plain=f'_001_{SECRET}'),
    ],
)
def test_invalid_api_key_raises_without_echoing_it(api_key):
    with pytest.raises(ValidationError) as caught:
        RedirectClient.from_api_key(api_key)
    assert str(caught.value) == 'API key is not valid.'
    assert caught.value.__cause__ is None and caught.value.__context__ is None


def test_api_key_environment_cannot_be_overridden():
    with pytest.raises(ValidationError):
        RedirectClient.from_api_key(_api_key('TEST'), sandbox=False)
    with pytest.raises(TypeError):
        RedirectClient.from_api_key(_api_key('TEST'), environment='PROD')


# == Secrets ==


@pytest.mark.parametrize('client_class', CLIENTS)
def test_repr_shows_no_secret(client_class):
    api_key = _api_key()
    client = client_class.from_api_key(api_key)
    text = repr(client)
    assert text.startswith(client_class.__name__)
    assert 'TEST' in text and MERCHANT_CODE in text
    assert SECRET not in text and api_key.partition('_')[2] not in text
