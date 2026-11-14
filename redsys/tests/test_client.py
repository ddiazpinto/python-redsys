import base64
import hmac
import json
from decimal import ROUND_HALF_UP
from decimal import Decimal as D
from unittest import mock

import pytest

from redsys import client as client_module
from redsys.client import RedirectClient
from redsys.constants import EUR
from redsys.constants import STANDARD_PAYMENT
from redsys.request import Request


class TestRedirectClient:
    @pytest.fixture(autouse=True)
    def set_up(self):
        secret_key = "sq7HjrUOBfKmC576ILgskD5srU870gJ7"
        self.client = RedirectClient(secret_key)
        self.parameters = {
            "merchant_code": "100000001",
            "terminal": "1",
            "transaction_type": STANDARD_PAYMENT,
            "currency": EUR,
            "order": "000000000001",
            "amount": D("10.56489").quantize(D(".01"), ROUND_HALF_UP),
            "merchant_data": "test merchant data",
            "merchant_name": "Example Commerce",
            "titular": "Example Ltd.",
            "product_description": "Products of Example Commerce",
            "merchant_url": "https://example.com/redsys/response",
        }
        self.request = Request(self.parameters)
        self.merchant_params = self.request.prepare_parameters()

    def test_encode_parameters(self):
        encoded_params = self.client.encode_parameters(self.merchant_params)
        encoded_params_str = encoded_params.decode("UTF-8")
        assert encoded_params_str.endswith("ZWRzeXMvcmVzcG9uc2UifQ==")
        assert len(encoded_params_str) == 628

    def test_decode_parameters(self):
        encoded_params = self.client.encode_parameters(self.merchant_params)
        decoded_params = self.client.decode_parameters(encoded_params)
        assert decoded_params == self.merchant_params

    def test_encrypt_3DES(self):
        encrypted_order = self.client.encrypt_3DES(self.request.order)
        assert len(encrypted_order) == 16
        assert str(encrypted_order) == "b'/\\x17\\\\6\\n\\x1aY\\xf3\\xd7\\xa5\\x97\\xb9\\xb6\\xe0\\x8dH'"

    def test_sign_hmac256(self):
        encrypted_order = self.client.encrypt_3DES(self.request.order)
        encoded_params = self.client.encode_parameters(self.merchant_params)
        signature = self.client.sign_hmac256(encrypted_order, encoded_params)
        assert signature == b"a2F05DwuH5aXu5vD1IdjQ+NxaR0lPsRwksW1nr2Nzuw="

    def test_prepare_request(self):
        prepared_request = self.client.prepare_request(self.parameters)
        assert len(prepared_request.keys()) == 3
        assert prepared_request.get("Ds_Signature") == b"a2F05DwuH5aXu5vD1IdjQ+NxaR0lPsRwksW1nr2Nzuw="
        pass

    def test_create_response_valid(self):
        merchant_parameters = {
            "Ds_MerchantCode": "100000001",
            "Ds_Terminal": "1",
            "Ds_TransactionType": "0",
            "Ds_Currency": 978,
            "Ds_Order": "000000000001",
            "Ds_Amount": 1056,
            "Ds_MerchantData": "test merchant data",
        }
        encoded_params = self.client.encode_parameters(merchant_parameters)
        signature = self.client.generate_signature(self.request.order, encoded_params)
        response = self.client.create_response(signature.decode(), encoded_params.decode())
        assert response._parameters.get("order") == merchant_parameters.get("Ds_Order")

    def test_create_response_invalid(self):
        merchant_parameters = {
            "Ds_MerchantCode": "100000001",
            "Ds_Terminal": "1",
            "Ds_TransactionType": "0",
            "Ds_Currency": 978,
            "Ds_Order": "000000000001",
            "Ds_Amount": 1056,
            "Ds_MerchantData": "test merchant data",
        }
        encoded_params = self.client.encode_parameters(merchant_parameters)
        bad_signature = b"sadfe2r3q2fdssaf3"
        with pytest.raises(ValueError, match="The provided signature is not valid"):
            self.client.create_response(bad_signature.decode(), encoded_params.decode())


SECRET = "sq7HjrUOBfKmC576ILgskD5srU870gJ7"
ORDER = "000000000001"


def _nested(depth):
    value = []
    for _ in range(depth - 1):
        value = [value]
    return value


class TestCreateResponseHardening:
    @pytest.fixture(autouse=True)
    def set_up(self):
        self.client = RedirectClient(SECRET)

    def _signed(self, fields, order=ORDER):
        encoded = self.client.encode_parameters(fields)
        return self.client.generate_signature(order, encoded).decode(), encoded.decode()

    def _unsigned(self, raw):
        return "x", base64.b64encode(raw).decode()

    @pytest.mark.parametrize(
        "signature, merchant_parameters",
        [
            (b"x", "e30="),
            ("A" * 129, "e30="),
            ("x", 7),
            ("x", "ée30="),
            ("x", "AAAA"),
            ("x", base64.b64encode(b"\xff\xfe").decode()),
            ("x", base64.b64encode(b"[1, 2]").decode()),
        ],
        ids=[
            "signature bytes",
            "signature too long",
            "parameters not text",
            "parameters not ascii",
            "not base64 json",
            "not utf-8",
            "json array",
        ],
    )
    def test_malformed_payload_raises_value_error(self, signature, merchant_parameters):
        with pytest.raises(ValueError) as raised:
            self.client.create_response(signature, merchant_parameters)
        assert "The provided signature is not valid" not in str(raised.value)

    def test_oversized_parameters_are_rejected_before_decoding(self, monkeypatch):
        signature, merchant_parameters = self._signed({"Ds_Order": ORDER, "Ds_Response": "0000"})
        monkeypatch.setattr(client_module, "_MAX_MERCHANT_PARAMETERS_LENGTH", len(merchant_parameters) - 1)
        with mock.patch.object(RedirectClient, "decode_parameters") as decode, pytest.raises(
            ValueError, match="at most"
        ):
            self.client.create_response(signature, merchant_parameters)
        decode.assert_not_called()

    def test_parameters_at_the_limit_are_accepted(self, monkeypatch):
        signature, merchant_parameters = self._signed({"Ds_Order": ORDER, "Ds_Response": "0000"})
        monkeypatch.setattr(client_module, "_MAX_MERCHANT_PARAMETERS_LENGTH", len(merchant_parameters))
        assert self.client.create_response(signature, merchant_parameters).is_paid

    def test_deep_nesting_is_rejected_before_parsing(self):
        raw = json.dumps({"Ds_Order": ORDER, "x": _nested(32)}).encode()
        with mock.patch("redsys.client.json.loads") as parse, pytest.raises(ValueError, match="nests deeper"):
            self.client.create_response(*self._unsigned(raw))
        parse.assert_not_called()

    def test_nesting_at_the_limit_is_accepted(self):
        signature, merchant_parameters = self._signed({"Ds_Order": ORDER, "Ds_Response": "0000", "x": _nested(31)})
        assert self.client.create_response(signature, merchant_parameters).is_paid

    @pytest.mark.parametrize(
        "text, depth",
        [
            ('{"a": "[[[[", "b": [1, {"c": "]]]]"}]}', 3),
            ('{"a": "x\\"[[", "b": "\\\\", "c": [[]], "d": "\\\\\\"]]"}', 3),
            ('{"a": "' + "]" * 40 + '", "b": ' + "[" * 30 + "]" * 30 + "}", 31),
        ],
    )
    def test_depth_ignores_brackets_inside_strings(self, text, depth):
        padded = ("[" + text + "," + ",".join(["[]"] * 40) + "]").encode()
        assert client_module._json_depth_exceeds(padded, depth + 1) is False
        assert client_module._json_depth_exceeds(padded, depth) is True

    @pytest.mark.parametrize("fields", [{"Ds_Response": "0000"}, {"Ds_Order": "1" * 20}, {"Ds_Order": 1}])
    def test_order_that_cannot_sign_fails_verification(self, fields):
        signature, merchant_parameters = self._signed(fields)
        with pytest.raises(ValueError, match="The provided signature is not valid"):
            self.client.create_response(signature, merchant_parameters)

    def test_fields_are_not_read_without_a_matching_signature(self):
        raw = json.dumps({"Ds_Order": ORDER, "Ds_Amount": "not a number"}).encode()
        invalid = pytest.raises(ValueError, match="The provided signature is not valid")
        with mock.patch("redsys.client.Response") as response, invalid:
            self.client.create_response(*self._unsigned(raw))
        response.assert_not_called()

    def test_signed_invalid_field_raises_value_error(self):
        signature, merchant_parameters = self._signed({"Ds_Order": ORDER, "Ds_Amount": "not a number"})
        with pytest.raises(ValueError, match="holds a field"):
            self.client.create_response(signature, merchant_parameters)

    def test_signatures_compare_in_constant_time(self):
        signature, merchant_parameters = self._signed({"Ds_Order": ORDER, "Ds_Response": "0000"})
        with mock.patch("redsys.client.hmac.compare_digest", wraps=hmac.compare_digest) as compare:
            self.client.create_response(signature, merchant_parameters)
        compare.assert_called_once()

    def test_url_safe_signature_is_accepted(self):
        signature, merchant_parameters = self._signed({"Ds_Order": ORDER, "Ds_Response": "0000", "Ds_Amount": "1056"})
        response = self.client.create_response(signature.replace("+", "-").replace("/", "_"), merchant_parameters)
        assert response.is_paid
        assert response.amount == D("10.56")
