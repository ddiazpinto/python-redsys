import re
from decimal import Decimal
from typing import Any, Dict

from redsys.constants import CURRENCIES, LANGUAGES, TRANSACTIONS

# General parameters
MERCHANT_CODE = "Ds_Merchant_MerchantCode"
TERMINAL = "Ds_Merchant_Terminal"
TRANSACTION_TYPE = "Ds_Merchant_TransactionType"
ORDER = "Ds_Merchant_Order"
CURRENCY = "Ds_Merchant_Currency"
AMOUNT = "Ds_Merchant_Amount"

# Recurring transaction parameters
SUM_TOTAL = "Ds_Merchant_SumTotal"
DATE_FREQUENCY = "Ds_Merchant_DateFrecuency"
CHARGE_EXPIRY_DATE = "Ds_Merchant_ChargeExpiryDate"
TRANSACTION_DATE = "Ds_Merchant_TransactionDate"
AUTHORIZATION_CODE = "Ds_Merchant_AuthorisationCode"

# Optional parameters
MERCHANT_DATA = "Ds_Merchant_MerchantData"

# Redirect client paramenters
MERCHANT_NAME = "Ds_Merchant_MerchantName"
PRODUCT_DESCRIPTION = "Ds_Merchant_ProductDescription"
TITULAR = "Ds_Merchant_Titular"
MERCHANT_URL = "Ds_Merchant_MerchantURL"
URL_OK = "Ds_Merchant_UrlOK"
URL_KO = "Ds_Merchant_UrlKO"
CONSUMER_LANGUAGE = "Ds_Merchant_ConsumerLanguage"

# Credit card data parameters
PAN = "Ds_Merchant_Pan"
EXPIRY_DATE = "Ds_Merchant_ExpiryDate"
CVV2 = "Ds_Merchant_Cvv2"

MERCHANT_PARAMETERS_MAP = {
    "merchant_code": MERCHANT_CODE,
    "terminal": TERMINAL,
    "transaction_type": TRANSACTION_TYPE,
    "order": ORDER,
    "currency": CURRENCY,
    "amount": AMOUNT,
    "sum_total": SUM_TOTAL,
    "date_frequency": DATE_FREQUENCY,
    "charge_expiry_date": CHARGE_EXPIRY_DATE,
    "transaction_date": TRANSACTION_DATE,
    "authorization_code": AUTHORIZATION_CODE,
    "merchant_data": MERCHANT_DATA,
    "merchant_name": MERCHANT_NAME,
    "product_description": PRODUCT_DESCRIPTION,
    "titular": TITULAR,
    "merchant_url": MERCHANT_URL,
    "url_ok": URL_OK,
    "url_ko": URL_KO,
    "consumer_language": CONSUMER_LANGUAGE,
    "pan": PAN,
    "expiry_date": EXPIRY_DATE,
    "cvv2": CVV2,
}


class Request:
    """
    Defines an atomic request with all the required parameters and sanitize
    their values according to the platform specifications
    """

    _parameters: Dict[str, Any] = {}

    def __init__(self, parameters: Dict[str, Any]) -> None:
        for key, value in parameters.items():
            if key in MERCHANT_PARAMETERS_MAP:
                if check := getattr(self, f"check_{str(key)}", None):
                    check(value)
                self._parameters[key] = value
            else:
                raise ValueError(f"Unknown parameter {key}")

    def __getattr__(self, item: str) -> Any:
        if item in MERCHANT_PARAMETERS_MAP:
            return self._parameters[item]

    def __setattr__(self, key, value):
        if key in MERCHANT_PARAMETERS_MAP:
            if check := getattr(self, "check_%s" % key, None):
                check(value)
            self._parameters[key] = value

    def prepare_parameters(self) -> Dict[str, str]:
        parameters = {}
        for key, value in self._parameters.items():
            prepare = getattr(self, "prepare_%s" % key, None)
            parameters[MERCHANT_PARAMETERS_MAP[key]] = (
                prepare(value) if prepare else value
            )
        return parameters

    @staticmethod
    def prepare_amount(value):
        return int(value * 100)

    @staticmethod
    def prepare_sum_total(value):
        return int(value * 100)

    @staticmethod
    def check_order(value):
        if not re.match(r"[0-9]{4}[a-zA-Z0-9]{5}$", value):
            raise ValueError("order format is not valid.")

    @staticmethod
    def check_transaction_type(value):
        if value not in TRANSACTIONS:
            raise ValueError("transaction_type is not valid.")

    @staticmethod
    def check_currency(value):
        if value not in CURRENCIES:
            raise ValueError("currency is not valid.")

    @staticmethod
    def check_amount(value):
        if not isinstance(value, Decimal):
            raise TypeError("amount must be defined as decimal.Decimal.")

    @staticmethod
    def check_sum_total(value):
        if type(value) is not Decimal:
            raise TypeError("sum_total must be defined as decimal.Decimal.")

    @staticmethod
    def check_merchant_data(value):
        if len(value) > 1024:
            raise ValueError("merchant_data cannot be longer than 1024 characters.")

    @staticmethod
    def check_merchant_url(value):
        if len(value) > 250:
            raise ValueError("merchant_url cannot be longer than 250 characters.")

    @staticmethod
    def check_url_ok(value):
        if len(value) > 250:
            raise ValueError("url_ok cannot be longer than 250 characters.")

    @staticmethod
    def check_url_ko(value):
        if len(value) > 250:
            raise ValueError("url_ko cannot be longer than 250 characters.")

    @staticmethod
    def check_consumer_language(value):
        if value not in LANGUAGES:
            raise ValueError("consumer_language is not valid.")
