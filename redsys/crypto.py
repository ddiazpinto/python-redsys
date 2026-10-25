"""Signature computation for the RedSys message envelope.

Every version derives a per-operation key by encrypting the order number under
the merchant secret, then HMACs the Base64 merchant parameters with that key.
They differ in cipher, padding, hash, and output encoding:

| Version          | Cipher  | Key                       | Order padding | HMAC    | Signature encoding      |
|------------------|---------|---------------------------|---------------|---------|-------------------------|
| HMAC_SHA256_V1   | 3DES    | Base64-decoded secret     | zero          | SHA-256 | Base64                  |
| HMAC_SHA512_V1   | AES-128 | first 16 chars of secret  | PKCS7         | SHA-512 | Base64URL, '=' kept     |
| HMAC_SHA512_V2   | AES-128 | first 16 chars of secret  | PKCS7         | SHA-512 | Base64URL, '=' stripped |

HMAC_SHA512_V2 also sends Ds_MerchantParameters as unpadded Base64URL; the other
versions send standard Base64. Responses are decoded tolerantly in either form.

The SHA-512 versions key their HMAC with the Base64 text of the derived key and differ
only in the padding of the signature (RedSys PHP library 2.0.1, Signature.php);
HMAC_SHA256_V1 uses the raw derived bytes.

HMAC_SHA512_V1 is the REST guide 4.0.1 scheme; HMAC_SHA512_V2 (the default) is the one the
redirection guide 4.1 and later and RedSys's own libraries use; HMAC_SHA256_V1 is
still accepted (REST guide 4.0.1, Anexo 2). The cipher parameters are pinned by a
known-answer test against RedSys's official worked example (see tests/test_crypto.py).
"""

from base64 import b64decode, b64encode, urlsafe_b64encode
from hashlib import sha256, sha512
from hmac import HMAC
from json import dumps

from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES  # 3DES, in decrepit since cryptography 43
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

HMAC_SHA256_V1 = 'HMAC_SHA256_V1'
HMAC_SHA512_V1 = 'HMAC_SHA512_V1'
HMAC_SHA512_V2 = 'HMAC_SHA512_V2'


class Signer:
    """Computes the signature for a single signature version."""

    version: str

    def __init__(self, secret_key: str):
        self._secret_key = secret_key

    def encode_parameters(self, parameters: dict) -> bytes:
        """Encode the wire dict as the Ds_MerchantParameters string this version expects."""
        return b64encode(dumps(parameters, sort_keys=True).encode('utf-8'))

    def _derive_key(self, order: str) -> bytes:
        raise NotImplementedError

    def sign(self, order: str, merchant_parameters: bytes) -> bytes:
        raise NotImplementedError


class Sha256V1Signer(Signer):
    version = HMAC_SHA256_V1

    def _derive_key(self, order: str) -> bytes:
        key = b64decode(self._secret_key)
        data = order.encode('utf-8')
        data += b'\x00' * (-len(data) % 8)  # zero-pad to the 3DES block
        encryptor = Cipher(TripleDES(key), modes.CBC(b'\x00' * 8)).encryptor()
        return encryptor.update(data) + encryptor.finalize()

    def sign(self, order: str, merchant_parameters: bytes) -> bytes:
        derived = self._derive_key(order)
        return b64encode(HMAC(derived, merchant_parameters, sha256).digest())


class Sha512V1Signer(Signer):
    version = HMAC_SHA512_V1

    def _derive_key(self, order: str) -> bytes:
        # Secret truncated to 16 chars, right-padded with '0' if shorter (REST manual v4.0.1).
        key = self._secret_key[:16].ljust(16, '0').encode('utf-8')
        padder = padding.PKCS7(128).padder()  # AES block size in bits
        data = padder.update(order.encode('utf-8')) + padder.finalize()
        encryptor = Cipher(algorithms.AES(key), modes.CBC(b'\x00' * 16)).encryptor()
        return encryptor.update(data) + encryptor.finalize()

    def sign(self, order: str, merchant_parameters: bytes) -> bytes:
        # The HMAC key is the Base64 text of the derived key, not its raw bytes
        # (confirmed live against the RedSys test environment; raw bytes -> SIS0042).
        derived = b64encode(self._derive_key(order))
        # REST manual: Base64URL with the '=' padding kept.
        return urlsafe_b64encode(HMAC(derived, merchant_parameters, sha512).digest())


class Sha512V2Signer(Sha512V1Signer):
    version = HMAC_SHA512_V2

    def encode_parameters(self, parameters: dict) -> bytes:
        # V2 endpoints decode Ds_MerchantParameters as unpadded Base64URL: the 3DS
        # initialization rejects standard or padded Base64 with SIS0430 (verified
        # live 2026-10-25), and the RedSys PHP library sends it this way.
        return urlsafe_b64encode(dumps(parameters, sort_keys=True).encode('utf-8')).rstrip(b'=')

    def sign(self, order: str, merchant_parameters: bytes) -> bytes:
        # Same derived key and HMAC as HMAC_SHA512_V1; only the '=' padding goes
        # (RedSys PHP library 2.0.1, base64_url_encode_safe).
        return super().sign(order, merchant_parameters).rstrip(b'=')


_SIGNERS = {
    HMAC_SHA256_V1: Sha256V1Signer,
    HMAC_SHA512_V1: Sha512V1Signer,
    HMAC_SHA512_V2: Sha512V2Signer,
}

SIGNATURE_VERSIONS = tuple(_SIGNERS)
DEFAULT_SIGNATURE_VERSION = HMAC_SHA512_V2


def get_signer(secret_key: str, signature_version: str = DEFAULT_SIGNATURE_VERSION) -> Signer:
    try:
        signer_class = _SIGNERS[signature_version]
    except KeyError:
        raise ValueError(f'Unsupported signature version: {signature_version!r}') from None
    return signer_class(secret_key)
