import os
import sys
from base64 import b64decode, b64encode
from hashlib import sha256
from hmac import HMAC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES  # 3DES, in decrepit since cryptography 43
from cryptography.hazmat.primitives.ciphers import Cipher, modes

from redsys.crypto import (
    DEFAULT_SIGNATURE_VERSION,
    HMAC_SHA256_V1,
    HMAC_SHA512_V1,
    HMAC_SHA512_V2,
    Sha256V1Signer,
    Sha512V1Signer,
    Sha512V2Signer,
    get_signer,
)

# Official RedSys sandbox secret key.
SECRET = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'


def test_sha512_derived_key_matches_official_example():
    # From RedSys's official "Firmar una operación" worked example:
    # first-16 chars of the secret + order '1234567890' -> RWt3/IPTzYRMXsQtkiGRKg==
    derived = Sha512V1Signer(SECRET)._derive_key('1234567890')
    assert b64encode(derived) == b'RWt3/IPTzYRMXsQtkiGRKg=='


def test_sha256_v1_matches_proven_original_algorithm():
    # The pre-refactor library signed successfully against real RedSys using
    # 3DES-CBC with the order zero-padded (ljust to 16). For a 9+ char order
    # that equals the canonical zero-pad to the block, so the signer must match.
    order = '123456789'
    merchant_parameters = b64encode(b'{"Ds_Merchant_Amount":1056}')

    key = b64decode(SECRET)
    encryptor = Cipher(TripleDES(key), modes.CBC(b'\x00' * 8)).encryptor()
    derived = encryptor.update(order.ljust(16, '\x00').encode('utf-8')) + encryptor.finalize()
    expected = b64encode(HMAC(derived, merchant_parameters, sha256).digest())

    assert Sha256V1Signer(SECRET).sign(order, merchant_parameters) == expected


def test_sha512_signature_is_padded_base64url():
    sig = Sha512V1Signer(SECRET).sign('1234567890', b64encode(b'{"a":"b"}'))
    assert b'+' not in sig and b'/' not in sig  # URL-safe alphabet
    assert sig.endswith(b'=')  # padding kept, per the REST manual v4.0.1


def test_get_signer_dispatch_and_default():
    assert isinstance(get_signer(SECRET, HMAC_SHA256_V1), Sha256V1Signer)
    assert isinstance(get_signer(SECRET, HMAC_SHA512_V1), Sha512V1Signer)
    assert isinstance(get_signer(SECRET, HMAC_SHA512_V2), Sha512V2Signer)
    assert DEFAULT_SIGNATURE_VERSION == HMAC_SHA512_V2
    try:
        get_signer(SECRET, 'NOPE_V9')
        raise AssertionError('expected ValueError for unknown version')
    except ValueError:
        pass


# Signed results returned by the live RedSys test environment (public test merchant
# 999008881, terminal 1, test card) for a full EMV3DS payment, one per signature
# version. Reproducing RedSys's own signature pins both schemes end to end.
LIVE_SHA512_V1_ORDER = '10022122197'
LIVE_SHA512_V1_PARAMETERS = b'eyJEc19BbW91bnQiOiIxMDAiLCJEc19DdXJyZW5jeSI6Ijk3OCIsIkRzX09yZGVyIjoiMTAwMjIxMjIxOTciLCJEc19NZXJjaGFudENvZGUiOiI5OTkwMDg4ODEiLCJEc19UZXJtaW5hbCI6IjEiLCJEc19SZXNwb25zZSI6IjAwMDAiLCJEc19BdXRob3Jpc2F0aW9uQ29kZSI6IjA1MjcyNSIsIkRzX1RyYW5zYWN0aW9uVHlwZSI6IjAiLCJEc19TZWN1cmVQYXltZW50IjoiMiIsIkRzX0xhbmd1YWdlIjoiMSIsIkRzX0NhcmROdW1iZXIiOiI0NTQ4ODEqKioqKiowMDAzIiwiRHNfTWVyY2hhbnREYXRhIjoiIiwiRHNfQ2FyZF9Db3VudHJ5IjoiNzI0IiwiRHNfQ2FyZF9UeXBvbG9neSI6IkNPTlNVTU8iLCJEc19DYXJkX0JyYW5kIjoiMSIsIkRzX1Byb2Nlc3NlZFBheU1ldGhvZCI6Ijc4IiwiRHNfQ29udHJvbF8xNzkwOTY4OTQ5OTU2IjoiMTc5MDk2ODk0OTk1NiIsIkRzX0VDSSI6IjA1IiwiRHNfUmVzcG9uc2VfRGVzY3JpcHRpb24iOiJPUEVSQUNJT04gQVVUT1JJWkFEQSJ9'  # noqa: E501
LIVE_SHA512_V1_SIGNATURE = b'2UjS7FS0cbemT8k7y7ixN6spuHLzaHoZKWG1bSXwvuqYBExilRvvneMYIkmuvCwdsMD_jTwZ1TU8gEZlAPeHrQ=='

LIVE_SHA256_V1_ORDER = '10022122318'
LIVE_SHA256_V1_PARAMETERS = b'eyJEc19BbW91bnQiOiIxMDAiLCJEc19DdXJyZW5jeSI6Ijk3OCIsIkRzX09yZGVyIjoiMTAwMjIxMjIzMTgiLCJEc19NZXJjaGFudENvZGUiOiI5OTkwMDg4ODEiLCJEc19UZXJtaW5hbCI6IjEiLCJEc19SZXNwb25zZSI6IjAwMDAiLCJEc19BdXRob3Jpc2F0aW9uQ29kZSI6IjA1MjcyNiIsIkRzX1RyYW5zYWN0aW9uVHlwZSI6IjAiLCJEc19TZWN1cmVQYXltZW50IjoiMiIsIkRzX0xhbmd1YWdlIjoiMSIsIkRzX0NhcmROdW1iZXIiOiI0NTQ4ODEqKioqKiowMDAzIiwiRHNfTWVyY2hhbnREYXRhIjoiIiwiRHNfQ2FyZF9Db3VudHJ5IjoiNzI0IiwiRHNfQ2FyZF9UeXBvbG9neSI6IkNPTlNVTU8iLCJEc19DYXJkX0JyYW5kIjoiMSIsIkRzX1Byb2Nlc3NlZFBheU1ldGhvZCI6Ijc4IiwiRHNfQ29udHJvbF8xNzkwOTY4OTY0NTk4IjoiMTc5MDk2ODk2NDU5OCIsIkRzX0VDSSI6IjA1IiwiRHNfUmVzcG9uc2VfRGVzY3JpcHRpb24iOiJPUEVSQUNJT04gQVVUT1JJWkFEQSJ9'  # noqa: E501
LIVE_SHA256_V1_SIGNATURE = b'jH4OTUXKiN6yt-AqyVBIov6xPvyFv5M8RnFk8uKeEFc='


def test_sha512_v1_reproduces_live_redsys_signature():
    assert Sha512V1Signer(SECRET).sign(LIVE_SHA512_V1_ORDER, LIVE_SHA512_V1_PARAMETERS) == LIVE_SHA512_V1_SIGNATURE


def test_sha256_v1_reproduces_live_redsys_signature():
    sig = Sha256V1Signer(SECRET).sign(LIVE_SHA256_V1_ORDER, LIVE_SHA256_V1_PARAMETERS)
    assert sig == LIVE_SHA256_V1_SIGNATURE.replace(b'-', b'+').replace(b'_', b'/')  # RedSys answers Base64URL


def test_sha512_v2_is_v1_without_padding():
    # RedSys PHP library 2.0.1: createMerchantSignature512V2 equals 512V1 except that
    # base64_url_encode_safe strips the '=' padding.
    params = b64encode(b'{"a":"b"}')
    v1 = Sha512V1Signer(SECRET).sign('1234567890', params)
    v2 = Sha512V2Signer(SECRET).sign('1234567890', params)
    assert v2 == v1.rstrip(b'=')
    assert b'=' not in v2 and len(v2) == 86  # 64-byte HMAC-SHA512, unpadded


def test_sha512_v2_matches_live_signature_unpadded():
    # The RedSys-signed live result under HMAC_SHA512_V1, minus padding, is its V2 form.
    sig = Sha512V2Signer(SECRET).sign(LIVE_SHA512_V1_ORDER, LIVE_SHA512_V1_PARAMETERS)
    assert sig == LIVE_SHA512_V1_SIGNATURE.rstrip(b'=')


def test_sha512_v2_response_round_trip():
    from redsys.clients import MERCHANT_PARAMETERS, SIGNATURE, SIGNATURE_VERSION, RedirectClient

    # V2 responses arrive as unpadded Base64URL; the library must decode and verify them.
    params = Sha512V2Signer(SECRET).encode_parameters({'Ds_Order': '000000000001', 'Ds_Response': '0000'})
    assert b'=' not in params
    payload = {
        SIGNATURE_VERSION: HMAC_SHA512_V2,
        MERCHANT_PARAMETERS: params.decode('utf-8'),
        SIGNATURE: Sha512V2Signer(SECRET).sign('000000000001', params).decode('utf-8'),
    }
    assert RedirectClient(SECRET).parse_response(payload).is_paid()


def test_sha512_v2_encodes_parameters_as_unpadded_base64url():
    # The 3DS initialization endpoint rejects standard or padded Base64 under V2 (SIS0430, live 2026-10-25).
    wire = {
        'Ds_Merchant_Order': '1234567890',
        'Ds_Merchant_Amount': 100,
        'Ds_Merchant_MerchantURL': 'https://x/?a=1&b=2',
    }
    v1 = Sha512V1Signer(SECRET).encode_parameters(wire)
    v2 = Sha512V2Signer(SECRET).encode_parameters(wire)
    assert b64decode(v1) == b64decode(v2.replace(b'-', b'+').replace(b'_', b'/') + b'=' * (-len(v2) % 4))
    assert b'=' not in v2 and b'+' not in v2 and b'/' not in v2
