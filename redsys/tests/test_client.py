import base64
import json
from decimal import ROUND_HALF_UP
from decimal import Decimal as D

import pytest

from redsys import currencies, transactions
from redsys.client import Client, RedirectClient


class TestClient:
    @pytest.fixture(autouse=True)
    def set_up(self):
        secret_key = "sq7HjrUOBfKmC576ILgskD5srU870gJ7"
        self.client = Client(secret_key)
        request = self.client.create_request()
        request.merchant_code = "100000001"
        request.terminal = "1"
        request.transaction_type = transactions.STANDARD_PAYMENT
        request.currency = currencies.EUR
        request.order = "000000001"
        request.amount = D("10.56489").quantize(D(".01"), ROUND_HALF_UP)
        request.merchant_data = "test merchant data"
        request.merchant_name = "Example Commerce"
        request.titular = "Example Ltd."
        request.product_description = "Products of Example Commerce"
        request.merchant_url = "https://example.com/redsys/response"
        self.request = request
        self.merchant_params = request.prepare_parameters()

    def test_encode_parameters(self):
        encoded_params = self.client.encode_parameters(self.merchant_params)
        encoded_params_str = encoded_params.decode("UTF-8")
        assert encoded_params_str.endswith("ZWRzeXMvcmVzcG9uc2UifQ==")
        assert len(encoded_params_str) == 624

    def test_decode_parameters(self):
        encoded_params = self.client.encode_parameters(self.merchant_params)
        decoded_params = self.client.decode_parameters(encoded_params)
        assert decoded_params == self.merchant_params

    def test_encrypt_3DES(self):
        encrypted_order = self.client.encrypt_3DES(self.request.order)
        assert len(encrypted_order) == 16
        assert (
            str(encrypted_order)
            == 'b"/\\x17\\\\6\\n\\x1aY\\xf3\\xb7\\\\\\xde\'d\\xa5\\x03\\xb7"'
        )

    def test_sign_hmac256(self):
        encrypted_order = self.client.encrypt_3DES(self.request.order)
        encoded_params = self.client.encode_parameters(self.merchant_params)
        signature = self.client.sign_hmac256(encrypted_order, encoded_params)
        assert signature == b"eEW4YN7/kkNHRO0/HhXy9TppzHwF38+eZApKAagDI9A="


class TestRedirectClient:
    @pytest.fixture(autouse=True)
    def set_up(self):
        secret_key = "sq7HjrUOBfKmC576ILgskD5srU870gJ7"
        self.client = RedirectClient(secret_key)
        request = self.client.create_request()
        request.merchant_code = "100000001"
        request.terminal = "1"
        request.transaction_type = transactions.STANDARD_PAYMENT
        request.currency = currencies.EUR
        request.order = "000000001"
        request.amount = D("10.56489").quantize(D(".01"), ROUND_HALF_UP)
        request.merchant_data = "test merchant data"
        request.merchant_name = "Example Commerce"
        request.titular = "Example Ltd."
        request.product_description = "Products of Example Commerce"
        request.merchant_url = "https://example.com/redsys/response"
        self.request = request

    def test_prepare_request(self):
        prepared_request = self.client.prepare_request(self.request)
        assert len(prepared_request.keys()) == 3
        assert (
            prepared_request.get("Ds_Signature")
            == b"eEW4YN7/kkNHRO0/HhXy9TppzHwF38+eZApKAagDI9A="
        )
        pass

    def test_create_response_valid(self):
        merchant_parameters = {
            "Ds_MerchantCode": "100000001",
            "Ds_Terminal": "1",
            "Ds_TransactionType": "0",
            "Ds_Currency": 978,
            "Ds_Order": "000000001",
            "Ds_Amount": 1056,
            "Ds_MerchantData": "test merchant data",
        }
        encoded_params = self.client.encode_parameters(merchant_parameters)
        signature = self.client.generate_signature(self.request.order, encoded_params)
        response = self.client.create_response(
            signature.decode(), encoded_params.decode()
        )
        assert response._parameters.get("order") == merchant_parameters.get("Ds_Order")

    def test_create_response_invalid(self):
        merchant_parameters = {
            "Ds_MerchantCode": "100000001",
            "Ds_Terminal": "1",
            "Ds_TransactionType": "0",
            "Ds_Currency": 978,
            "Ds_Order": "000000001",
            "Ds_Amount": 1056,
            "Ds_MerchantData": "test merchant data",
        }
        encoded_params = self.client.encode_parameters(merchant_parameters)
        bad_signature = b"sadfe2r3q2fdssaf3"
        with pytest.raises(ValueError, match="The provided signature is not valid"):
            response = self.client.create_response(
                bad_signature.decode(), encoded_params.decode()
            )
