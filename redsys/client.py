# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import re
from abc import ABCMeta, abstractmethod

from Crypto.Cipher import DES3

from redsys.request import Request
from redsys.response import Response

# Calculated parameters
SIGNATURE_VERSION = "Ds_SignatureVersion"
MERCHANT_PARAMETERS = "Ds_MerchantParameters"
SIGNATURE = "Ds_Signature"
DEFAULT_SIGNATURE_VERSION = "HMAC_SHA256_V1"


class Client(object):
    __metaclass__ = ABCMeta

    def __init__(self, secret_key=None):
        self.secret_key = secret_key

    def create_request(self):
        return Request()

    @abstractmethod
    def create_response(
        self, signature, parameters, signature_version=DEFAULT_SIGNATURE_VERSION
    ):
        raise NotImplementedError

    @abstractmethod
    def prepare_request(self, request):
        raise NotImplementedError

    def encode_parameters(self, parameters):
        """Encodes the merchant parameters in base64"""
        return base64.b64encode(json.dumps(parameters).encode())

    def decode_parameters(self, parameters):
        """Decodes the merchant parameters from base64"""
        return json.loads(base64.b64decode(parameters).decode())

    def encrypt_3DES(self, order):
        """Encrypts(3DES algorithm) the payment order using the secret key"""
        cipher = DES3.new(
            base64.b64decode(self.secret_key), DES3.MODE_CBC, IV=b"\0\0\0\0\0\0\0\0"
        )
        # the cipher needs to be passed 16 bytes,
        # so "order" must be 16 bytes long,
        # therefore we left-justify adding ceros
        return cipher.encrypt(order.encode().ljust(16, b"\0"))

    def sign_hmac256(self, encrypted_order, merchant_parameters):
        """
        Generates the encrypted signature using the encrypted order
        and merchant parameters
        """
        signature = hmac.new(
            encrypted_order, merchant_parameters, hashlib.sha256
        ).digest()
        return base64.b64encode(signature)

    def generate_signature(self, order, merchant_parameters):
        return self.sign_hmac256(self.encrypt_3DES(order), merchant_parameters)


class RedirectClient(Client):
    def prepare_request(self, request):
        """Takes the merchant parameters and returns the necessary parameters
        to make the POST request to Redsys"""
        merchant_parameters = self.encode_parameters(request.prepare_parameters())
        signature = self.generate_signature(request.order, merchant_parameters)
        return {
            SIGNATURE_VERSION: DEFAULT_SIGNATURE_VERSION,
            MERCHANT_PARAMETERS: merchant_parameters,
            SIGNATURE: signature,
        }

    def create_response(
        self,
        signature,
        merchant_parameters,
    ):
        """
        Decodes the Redsys response to check for validity.
        Checks if the received signature corresponds to the sent signature.

        Both the signature and merchant parameters are plain strings, not bytes.
        """
        decoded_parameters = self.decode_parameters(merchant_parameters)
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
