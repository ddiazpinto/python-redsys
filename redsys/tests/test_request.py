from decimal import ROUND_HALF_UP
from decimal import Decimal as D

import pytest

from redsys.constants import EUR, STANDARD_PAYMENT
from redsys.request import Request


class TestRequest:
    def test_create_request(self):
        parameters = {
            "merchant_code": "100000001",
            "terminal": "1",
            "transaction_type": STANDARD_PAYMENT,
            "currency": EUR,
            "order": "000000001",
            "amount": D("10.56489").quantize(D(".01"), ROUND_HALF_UP),
            "merchant_data": "test merchant data",
            "merchant_name": "Example Commerce",
            "titular": "Example Ltd.",
            "product_description": "Products of Example Commerce",
            "merchant_url": "https://example.com/redsys/response",
        }
        self.request = Request(parameters)
        assert self.request.product_description == "Products of Example Commerce"

    def test_bad_request_parameters(self):
        parameters = {
            "merchant_code": "100000001",
            "terminal": "1",
            "bad_key": "test",
        }
        with pytest.raises(ValueError, match="Unknown parameter"):
            self.request = Request(parameters)

    def test_prepare_parameters(self):
        parameters = {
            "merchant_code": "100000001",
            "terminal": "1",
            "transaction_type": STANDARD_PAYMENT,
            "currency": EUR,
            "order": "000000001",
            "amount": D("10.56489").quantize(D(".01"), ROUND_HALF_UP),
            "merchant_data": "test merchant data",
            "merchant_name": "Example Commerce",
            "titular": "Example Ltd.",
            "product_description": "Products of Example Commerce",
            "merchant_url": "https://example.com/redsys/response",
        }
        prepared_parameters = Request(parameters).prepare_parameters()
        assert len(prepared_parameters.keys()) == 11
        assert (
            prepared_parameters.get("Ds_Merchant_MerchantData") == "test merchant data"
        )
