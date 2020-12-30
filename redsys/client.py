import base64
import hashlib
import hmac
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict

from Crypto.Cipher import DES3

from redsys.request import Request
from redsys.response import Response

# Calculated parameters
SIGNATURE_VERSION = "Ds_SignatureVersion"
MERCHANT_PARAMETERS = "Ds_MerchantParameters"
SIGNATURE = "Ds_Signature"
DEFAULT_SIGNATURE_VERSION = "HMAC_SHA256_V1"


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
        """Decodes the merchant parameters from base64"""
        return json.loads(base64.b64decode(parameters).decode())

    @staticmethod
    def sign_hmac256(encrypted_order: bytes, merchant_parameters: bytes) -> bytes:
        """
        Generates the encrypted signature using the 3DES-encrypted order
        and base64-encoded merchant parameters
        """
        signature = hmac.new(
            encrypted_order, merchant_parameters, hashlib.sha256
        ).digest()
        return base64.b64encode(signature)

    def encrypt_3DES(self, order: str) -> bytes:
        """Encrypts(3DES algorithm) the payment order using the secret key"""
        cipher = DES3.new(
            base64.b64decode(self.secret_key), DES3.MODE_CBC, IV=b"\0\0\0\0\0\0\0\0"
        )
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
        """
        decoded_parameters = self.decode_parameters(merchant_parameters.encode())
        response = Response(decoded_parameters)
        calculated_signature = self.generate_signature(
            response.order, merchant_parameters.encode()
        )
        # Remove any non-alphanumeric characters from the signature
        not_alphanumeric = re.compile("[^a-zA-Z0-9]")
        safe_signature = re.sub(not_alphanumeric, "", signature)

        safe_calculated_signature = re.sub(
            not_alphanumeric, "", calculated_signature.decode()
        )
        if safe_signature != safe_calculated_signature:
            raise ValueError("The provided signature is not valid.")
        return response
