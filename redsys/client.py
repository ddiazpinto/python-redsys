# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import re
import sys
from abc import ABCMeta, abstractmethod

from Crypto.Cipher import DES3

from .request import Request
from .response import Response

# Calculated parameters
SIGNATURE_VERSION = "Ds_SignatureVersion"
MERCHANT_PARAMETERS = "Ds_MerchantParameters"
SIGNATURE = "Ds_Signature"
DEFAULT_SIGNATURE_VERSION = "HMAC_SHA256_V1"


class Client(object):
    __metaclass__ = ABCMeta

    def __init__(self, secret_key=None, sandbox=False):
        self.secret_key = secret_key
        self.endpoint = self.TEST_ENDPOINT if sandbox else self.REAL_ENDPOINT

    def create_request(self):
        return Request()

    @abstractmethod
    def create_response(
        self, signature, parameters, signature_version=DEFAULT_SIGNATURE_VERSION
    ):
        raise NotImplemented

    @abstractmethod
    def prepare_request(self, request):
        raise NotImplemented

    def encode_parameters(self, parameters):
        return base64.b64encode(json.dumps(parameters).encode("utf-8"))

    def decode_parameters(self, parameters):
        return json.loads(base64.b64decode(parameters).decode("utf-8"))

    def encrypt_3DES(self, order):
        pycrypto = DES3.new(
            base64.b64decode(self.secret_key), DES3.MODE_CBC, IV=b"\0\0\0\0\0\0\0\0"
        )
        if sys.version_info > (3, 0):
            order_padded = order.ljust(16, u"\x00")
        else:
            order_padded = order.ljust(16, b"\0")

        return pycrypto.encrypt(order_padded)

    def sign_hmac256(self, encrypted_order, merchant_parameters):
        signature = hmac.new(
            encrypted_order, merchant_parameters, hashlib.sha256
        ).digest()
        return base64.b64encode(signature)

    def generate_signature(self, order, merchant_parameters):
        return self.sign_hmac256(self.encrypt_3DES(order), merchant_parameters)


class RedirectClient(Client):
    def create_response(
        self,
        signature,
        merchant_parameters,
        signature_version=DEFAULT_SIGNATURE_VERSION,
    ):
        response = Response(self.decode_parameters(merchant_parameters))
        calculated_signature = self.generate_signature(
            response.order, merchant_parameters.encode("utf-8")
        )
        alphanum = re.compile("[^a-zA-Z0-9]")
        safe_signature = re.sub(alphanum, "", signature)
        safe_calculated_signature = re.sub(
            alphanum, "", calculated_signature.decode("utf-8")
        )
        if safe_signature != safe_calculated_signature:
            raise ValueError("The provided signature is not valid.")
        return response

    def prepare_request(self, request):
        merchant_parameters = self.encode_parameters(request.prepare_parameters())
        signature = self.sign_hmac256(
            self.encrypt_3DES(request.order), merchant_parameters
        )
        return {
            SIGNATURE_VERSION: DEFAULT_SIGNATURE_VERSION,
            MERCHANT_PARAMETERS: merchant_parameters,
            SIGNATURE: signature,
        }
