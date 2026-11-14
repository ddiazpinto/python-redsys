import base64
import hashlib
import hmac
import json
import re
from abc import ABC
from abc import abstractmethod
from itertools import accumulate
from operator import sub as subtract
from typing import Any
from typing import Dict

from Crypto.Cipher import DES3

from redsys.request import Request
from redsys.response import ORDER
from redsys.response import Response

# Calculated parameters
SIGNATURE_VERSION = "Ds_SignatureVersion"
MERCHANT_PARAMETERS = "Ds_MerchantParameters"
SIGNATURE = "Ds_Signature"
DEFAULT_SIGNATURE_VERSION = "HMAC_SHA256_V1"

# Real notifications take a few KiB; the caps bound the work done before the signature is checked.
_MAX_MERCHANT_PARAMETERS_LENGTH = 128 * 1024
_MAX_SIGNATURE_LENGTH = 128
# RedSys payloads nest two or three levels; deeper JSON can exhaust a small thread
# stack inside the C JSON decoder and kill the process.
_MAX_JSON_DEPTH = 32
_NOT_BRACKETS = bytes(sorted(set(range(256)) - set(b"[]{}")))
_BRACKET_WEIGHTS = bytes.maketrans(b"[{]}", b"\x02\x02\x00\x00")
_NOT_ALPHANUMERIC = re.compile(b"[^a-zA-Z0-9]")


def _json_depth_exceeds(text: bytes, limit: int) -> bool:
    """Whether JSON text nests deeper than ``limit``; brackets inside strings do not count."""
    if text.count(b"[") + text.count(b"{") <= limit:
        return False
    # Bytes operations only: the text may be attacker-sized, and a byte loop costs ten times more.
    outside_strings = b"".join(text.replace(b"\\\\", b"").replace(b'\\"', b"").split(b'"')[::2])
    # Opening brackets weigh 2 and closing ones 0: the running sum minus the position is the depth.
    weights = outside_strings.translate(_BRACKET_WEIGHTS, _NOT_BRACKETS)
    return max(map(subtract, accumulate(weights), range(1, len(weights) + 1)), default=0) > limit


def _received_field(value: str, name: str, max_length: int) -> bytes:
    """A received Base64 field as bytes; Base64 is ASCII text."""
    if not isinstance(value, str) or len(value) > max_length or not value.isascii():
        raise ValueError(f"{name} is not Base64 text of at most {max_length} characters.")
    return value.encode()


class Client(ABC):
    """
    Abstract class from which RedirectClient inherits.
    It implements methods that may be used in future clients(i.e. rest).
    """

    def __init__(self, secret_key: str):
        self.secret_key: bytes = secret_key.encode()

    @abstractmethod
    def create_response(self, signature, parameters):
        raise NotImplementedError

    @abstractmethod
    def prepare_request(self, request):
        raise NotImplementedError

    @staticmethod
    def encode_parameters(parameters: Dict[str, Any]) -> bytes:
        """Encodes the merchant parameters in base64"""
        return base64.b64encode(json.dumps(parameters).encode())

    @staticmethod
    def decode_parameters(parameters: bytes) -> Dict[str, Any]:
        """Decodes the merchant parameters from base64; JSON nested deeper than any RedSys payload raises ValueError"""
        text = base64.b64decode(parameters)
        if _json_depth_exceeds(text, _MAX_JSON_DEPTH):
            raise ValueError(f"JSON nests deeper than {_MAX_JSON_DEPTH} levels.")
        return json.loads(text.decode())

    @staticmethod
    def sign_hmac256(encrypted_order: bytes, merchant_parameters: bytes) -> bytes:
        """
        Generates the encrypted signature using the 3DES-encrypted order
        and base64-encoded merchant parameters
        """
        signature = hmac.new(encrypted_order, merchant_parameters, hashlib.sha256).digest()
        return base64.b64encode(signature)

    def encrypt_3DES(self, order: str) -> bytes:
        """Encrypts(3DES algorithm) the payment order using the secret key"""
        cipher = DES3.new(base64.b64decode(self.secret_key), DES3.MODE_CBC, IV=b"\0\0\0\0\0\0\0\0")
        # the cipher needs to be passed 16 bytes,
        # so "order" must be 16 bytes long,
        # therefore we left-justify adding ceros
        return cipher.encrypt(order.encode().ljust(16, b"\0"))

    def generate_signature(self, order: str, merchant_parameters: bytes) -> bytes:
        return self.sign_hmac256(self.encrypt_3DES(order), merchant_parameters)


class RedirectClient(Client):
    def prepare_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Takes the merchant parameters and returns the necessary parameters
        to make the POST request to Redsys"""
        request = Request(parameters)
        merchant_parameters = self.encode_parameters(request.prepare_parameters())
        signature = self.generate_signature(request.order, merchant_parameters)
        return {
            SIGNATURE_VERSION: DEFAULT_SIGNATURE_VERSION,
            MERCHANT_PARAMETERS: merchant_parameters,
            SIGNATURE: signature,
        }

    def create_response(
        self,
        signature: str,
        merchant_parameters: str,
    ) -> Response:
        """
        Decodes the Redsys response to check for validity.
        Checks if the received signature corresponds to the sent signature.

        Both the `signature` and `merchant parameters` are plain strings, not bytes.
        The fields are read only after the signature matches; a malformed payload
        raises `ValueError` too.
        """
        received_signature = _received_field(signature, SIGNATURE, _MAX_SIGNATURE_LENGTH)
        encoded_parameters = _received_field(merchant_parameters, MERCHANT_PARAMETERS, _MAX_MERCHANT_PARAMETERS_LENGTH)
        try:
            decoded_parameters = self.decode_parameters(encoded_parameters)
        except ValueError as error:
            raise ValueError(f"{MERCHANT_PARAMETERS} is not a Base64-encoded JSON object: {error}") from error
        if not isinstance(decoded_parameters, dict):
            raise ValueError(f"{MERCHANT_PARAMETERS} is not a Base64-encoded JSON object.")
        order = decoded_parameters.get(ORDER)
        # encrypt_3DES takes at most 16 ASCII bytes; any other order cannot verify, so it signs as ''.
        if not (isinstance(order, str) and order.isascii() and len(order) <= 16):
            order = ""
        calculated_signature = self.generate_signature(order, encoded_parameters)
        # Signatures may arrive in URL-safe Base64; only the alphanumeric core is compared.
        if not hmac.compare_digest(
            _NOT_ALPHANUMERIC.sub(b"", received_signature), _NOT_ALPHANUMERIC.sub(b"", calculated_signature)
        ):
            raise ValueError("The provided signature is not valid.")
        try:
            return Response(decoded_parameters)
        except (ValueError, ArithmeticError) as error:
            raise ValueError(f"{MERCHANT_PARAMETERS} holds a field that is not valid.") from error
