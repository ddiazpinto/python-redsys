from decimal import Decimal

from redsys.response import Response


class TestResponse:
    def test_create_response(self):
        parameters = {
            "Ds_Response": "90",
            "Ds_MerchantCode": "1056",
            "Ds_Terminal": "1",
            "Ds_TransactionType": "1",
            "Ds_Order": "000000000001",
            "Ds_Amount": "10054",
            "Ds_MerchantData": "test merchant data",
            "Ds_Currency": 978,
        }
        response = Response(parameters)
        assert response.code == 90
        assert response.message == "Transacción autorizada para pagos y preautorizaciones"
        assert len(response._parameters.keys()) == 8
        assert response.is_authorized is True
        assert response.is_paid is True
        assert response.is_canceled is False
        assert response.is_refunded is False

    def test_responses_do_not_share_parameters(self):
        first = Response({"Ds_Response": "0000", "Ds_Order": "000000000001", "Ds_Amount": "100"})
        second = Response({"Ds_Response": "0190", "Ds_Order": "000000000002"})
        assert "amount" not in second.parameters
        assert second.amount is None
        assert first.amount == Decimal("1.00")
