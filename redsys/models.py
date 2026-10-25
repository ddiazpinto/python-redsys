"""Declarative request and response models.

Each field carries its RedSys wire name as a Pydantic alias, so a message serializes to the
``Ds_Merchant_*`` dict with ``model_dump(by_alias=True)`` and a response parses from the ``Ds_*``
dict with ``model_validate``. Field constraints follow these RedSys documents:

- TPV Virtual, Manual de Integración - Redirección, RS.TE.CEL.MAN.0039, version 4.2 (2026-02-04),
  https://pagosonline.redsys.es/download/1735/
- TPV Virtual, Manual de Integración REST, RS.TE.CEL.MAN.0037, version 4.0.1 (2025-10-17),
  https://pagosonline.redsys.es/download/1738/
- Guía de integración de Bizum, version 2.6 (2026-08-25), https://pagosonline.redsys.es/download/2053/
- Developer portal pages "Firmar una operación", "Parámetros de entrada y salida" and "Operativa DCC".
- Librería de integración en PHP 2.0.1 (https://pagosonline.redsys.es/download/3214/), the reference
  for the response fields the guides omit.
"""

from base64 import b64decode, b64encode
from decimal import Decimal
from json import dumps, loads
from typing import Any
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from redsys.api.currencies import CURRENCIES, CURRENCY_DECIMALS
from redsys.api.transactions import TRANSACTION_TYPES
from redsys.exceptions import UnknownParameterWarning

# 1.x request names that changed or went away in 2.0; the error names the replacement.
_LEGACY_FIELDS: dict[str, str | None] = {
    'payment_method': 'pay_methods',
    'mobile_number': 'bizum_mobile_number',
    'transaction_date': None,
}


def decode_merchant_parameters(data: bytes) -> dict:
    """Decode a Ds_MerchantParameters string in standard or URL-safe Base64, padded or not.

    RedSys mixes the forms by signature version (HMAC_SHA512_V2 responses come unpadded).
    """
    data = data.replace(b'-', b'+').replace(b'_', b'/')
    return loads(b64decode(data + b'=' * (-len(data) % 4)).decode('utf-8'))


def minor_units_factor(currency: int | None) -> int:
    """Power-of-ten factor that converts major units to the wire minor units."""
    decimals = CURRENCY_DECIMALS.get(currency, 2) if currency is not None else 2
    return 10**decimals


class BaseRequest(BaseModel):
    """Fields common to every operation message, with validation and wire serialization."""

    # Construct with the snake_case names or the wire names; unknown names are screened below.
    model_config = ConfigDict(populate_by_name=True, extra='allow')

    merchant_code: str = Field(alias='Ds_Merchant_MerchantCode', max_length=9)
    terminal: int = Field(alias='Ds_Merchant_Terminal', ge=1, le=999)
    transaction_type: int = Field(0, alias='Ds_Merchant_TransactionType')
    amount: Decimal = Field(alias='Ds_Merchant_Amount', description='Major units; scaled to minor units on the wire.')
    currency: int = Field(alias='Ds_Merchant_Currency')
    order: str = Field(alias='Ds_Merchant_Order', min_length=4, max_length=12, pattern=r'^[0-9]{4}[a-zA-Z0-9]{0,8}$')
    merchant_data: str | None = Field(None, alias='Ds_Merchant_MerchantData', max_length=1024)

    @model_validator(mode='before')
    @classmethod
    def _screen_unknown_fields(cls, data: Any) -> Any:
        """Reject typos and 1.x names; let unmodeled RedSys wire names through with a warning.

        A parameter the library does not model yet is accepted under its wire
        name (``Ds_Merchant_*``) and sent as given, so a RedSys addition does not
        wait for a library release. Any other unknown name is a mistake and fails.
        """
        if not isinstance(data, dict):
            return data
        known = {name for name in cls.model_fields} | {f.alias for f in cls.model_fields.values() if f.alias}
        for key in data:
            if key in known:
                continue
            if key in _LEGACY_FIELDS:
                replacement = _LEGACY_FIELDS[key]
                hint = f'use {replacement!r}' if replacement else 'it has no 2.x equivalent'
                raise ValueError(f'{key!r} is a 1.x field name; {hint}.')
            if key.lower().startswith('ds_merchant_'):
                warn(f'{key!r} is not modeled by this library; sent as given.', UnknownParameterWarning, stacklevel=2)
                continue
            raise ValueError(f'unknown field {key!r}; pass unmodeled parameters by their wire name (Ds_Merchant_*).')
        return data

    @field_validator('transaction_type')
    @classmethod
    def _validate_transaction_type(cls, value: int) -> int:
        if value not in TRANSACTION_TYPES:
            raise ValueError('transaction_type is not valid.')
        return value

    @field_validator('currency')
    @classmethod
    def _validate_currency(cls, value: int) -> int:
        if value not in CURRENCIES:
            raise ValueError('currency is not valid.')
        return value

    @field_serializer('amount')
    def _serialize_amount(self, value: Decimal) -> int:
        return int(value * minor_units_factor(self.currency))

    def get_order(self) -> str:
        return self.order

    def prepare_parameters(self) -> dict:
        """The request as the RedSys wire dict (``Ds_Merchant_*`` keys)."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def encode(self) -> bytes:
        return b64encode(dumps(self.prepare_parameters(), sort_keys=True).encode('utf-8'))


class _RedirectFields(BaseModel):
    """Fields of the redirect connection (browser form)."""

    merchant_url: str | None = Field(None, alias='Ds_Merchant_MerchantURL', max_length=250)
    url_ok: str | None = Field(None, alias='Ds_Merchant_UrlOK', max_length=250)
    url_ko: str | None = Field(None, alias='Ds_Merchant_UrlKO', max_length=250)
    merchant_name: str | None = Field(None, alias='Ds_Merchant_MerchantName', max_length=25)
    product_description: str | None = Field(None, alias='Ds_Merchant_ProductDescription', max_length=125)
    titular: str | None = Field(None, alias='Ds_Merchant_Titular', max_length=60)
    consumer_language: int | None = Field(None, alias='Ds_Merchant_ConsumerLanguage')
    pay_methods: str | None = Field(None, alias='Ds_Merchant_PayMethods', description='"z" selects Bizum.')
    bizum_mobile_number: str | None = Field(None, alias='Ds_Merchant_Bizum_MobileNumber', max_length=19)
    excep_sca: str | None = Field(
        None,
        alias='Ds_Merchant_Excep_SCA',
        max_length=3,
        description='PSD2 SCA exemption requested; codes in redsys.api.sca.',
    )


class _DirectFields(BaseModel):
    """Fields of the direct connection (server-to-server card data, 3DS, stored credentials)."""

    pan: str | None = Field(None, alias='Ds_Merchant_Pan', max_length=19, pattern=r'^[0-9]{12,19}$')
    expiry_date: str | None = Field(None, alias='Ds_Merchant_ExpiryDate', pattern=r'^[0-9]{4}$', description='YYMM.')
    cvv2: str | None = Field(None, alias='Ds_Merchant_Cvv2', pattern=r'^[0-9]{3,4}$')
    identifier: str | None = Field(
        None, alias='Ds_Merchant_Identifier', max_length=40, description='Stored-card token; see redsys.api.cof.'
    )
    idoper: str | None = Field(None, alias='Ds_Merchant_Idoper', max_length=40, description='inSite operation token.')
    direct_payment: str | None = Field(None, alias='Ds_Merchant_DirectPayment', description='"true" or "moto".')
    emv3ds: dict[str, Any] | None = Field(None, alias='Ds_Merchant_EMV3DS', description='Build with redsys.threeds.')
    cof_ini: str | None = Field(None, alias='Ds_Merchant_Cof_Ini', max_length=1, description='See redsys.api.cof.')
    cof_type: str | None = Field(None, alias='Ds_Merchant_Cof_Type', max_length=1, description='See redsys.api.cof.')
    cof_txnid: str | None = Field(None, alias='Ds_Merchant_Cof_Txnid', max_length=15)
    # RedSys spells the wire name "Frecuency".
    date_frequency: str | None = Field(None, alias='Ds_Merchant_DateFrecuency', description='Days between charges.')
    charge_expiry_date: str | None = Field(None, alias='Ds_Merchant_ChargeExpiryDate', description='yyyy-MM-dd.')
    excep_sca: str | None = Field(
        None,
        alias='Ds_Merchant_Excep_SCA',
        max_length=3,
        description='PSD2 SCA exemption requested; codes in redsys.api.sca. "Y" on the 3DS initialization asks.',
    )


class RedirectPaymentMessage(BaseRequest, _RedirectFields):
    """Redirect-connection payment (transaction type 0)."""


class RedirectPreauthorizationMessage(BaseRequest, _RedirectFields):
    """Redirect-connection preauthorization (transaction type 1)."""

    transaction_type: int = Field(1, alias='Ds_Merchant_TransactionType')


class DirectPaymentMessage(BaseRequest, _DirectFields):
    """Direct-connection card payment (transaction type 0)."""

    sum_total: Decimal | None = Field(
        None, alias='Ds_Merchant_SumTotal', description='Recurring series total; scaled like amount.'
    )

    @field_serializer('sum_total')
    def _serialize_sum_total(self, value: Decimal | None) -> int | None:
        return int(value * minor_units_factor(self.currency)) if value is not None else None


class DirectPreauthorizationMessage(BaseRequest, _DirectFields):
    """Direct-connection preauthorization (transaction type 1)."""

    transaction_type: int = Field(1, alias='Ds_Merchant_TransactionType')


class ConfirmationMessage(BaseRequest):
    """Capture of a previous preauthorization (transaction type 2)."""

    transaction_type: int = Field(2, alias='Ds_Merchant_TransactionType')


class RefundMessage(BaseRequest):
    """Refund of a previous payment (transaction type 3)."""

    transaction_type: int = Field(3, alias='Ds_Merchant_TransactionType')
    authorization_code: str | None = Field(None, alias='Ds_Merchant_AuthorisationCode', max_length=6)


class CancellationMessage(BaseRequest):
    """Cancellation of a preauthorization (transaction type 9)."""

    transaction_type: int = Field(9, alias='Ds_Merchant_TransactionType')


class Response(BaseModel):
    """A parsed RedSys response with the standard result predicates.

    Every field is optional; presence varies by operation and outcome. Parameters the
    library does not list are kept, under their wire name, in ``model_extra``.
    """

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    response: str | None = Field(None, alias='Ds_Response', description='Result code, 4 digits.')
    amount: Decimal | None = Field(None, alias='Ds_Amount', description='Scaled from minor units by currency.')
    amount_euro: str | None = Field(None, alias='Ds_Amount_Euro', description='Raw wire value; non-euro operations.')
    date: str | None = Field(None, alias='Ds_Date')
    hour: str | None = Field(None, alias='Ds_Hour')
    merchant_code: str | None = Field(None, alias='Ds_MerchantCode')
    terminal: str | None = Field(None, alias='Ds_Terminal')
    transaction_type: str | None = Field(None, alias='Ds_TransactionType')
    order: str | None = Field(None, alias='Ds_Order')
    currency: int | None = Field(None, alias='Ds_Currency')
    merchant_data: str | None = Field(None, alias='Ds_MerchantData')
    consumer_language: str | None = Field(None, alias='Ds_ConsumerLanguage', description='Redirect notification.')
    language: str | None = Field(None, alias='Ds_Language', description='REST responses.')
    card_country: str | None = Field(None, alias='Ds_Card_Country')
    card_type: str | None = Field(None, alias='Ds_Card_Type')
    card_brand: str | None = Field(None, alias='Ds_Card_Brand')
    # Not in the integration guides: returned by the test environment (verified 2026-10-25)
    # and modeled by the official PHP library 2.0.1.
    card_typology: str | None = Field(None, alias='Ds_Card_Typology', description='For example CONSUMO.')
    eci: str | None = Field(None, alias='Ds_ECI', description='E-commerce indicator of the authentication.')
    response_description: str | None = Field(None, alias='Ds_Response_Description')
    secure_payment: str | None = Field(None, alias='Ds_SecurePayment')
    authorization_code: str | None = Field(None, alias='Ds_AuthorisationCode')
    error_code: str | None = Field(None, alias='Ds_ErrorCode')
    card_number: str | None = Field(None, alias='Ds_CardNumber')
    expiry_date: str | None = Field(None, alias='Ds_ExpiryDate')
    card_psd2: str | None = Field(None, alias='Ds_Card_PSD2')
    excep_sca: str | None = Field(
        None, alias='Ds_Excep_SCA', description='Exemptions the card allows, from the 3DS initialization.'
    )
    emv3ds: dict[str, Any] | None = Field(None, alias='Ds_EMV3DS')
    identifier: str | None = Field(None, alias='Ds_Merchant_Identifier', description='Token returned on request.')
    cof_txnid: str | None = Field(None, alias='Ds_Merchant_Cof_Txnid')
    processed_pay_method: str | None = Field(None, alias='Ds_ProcessedPayMethod', description='68 = Bizum.')
    bizum_id_oper: str | None = Field(None, alias='Ds_Bizum_IdOper')
    bizum_cuenta_truncada: str | None = Field(None, alias='Ds_Bizum_CuentaTruncada')
    currency_dcc: str | None = Field(None, alias='Ds_Currency_DCC', description='Dynamic currency conversion.')
    amount_dcc: str | None = Field(None, alias='Ds_Amount_DCC', description='Minor units in Ds_Currency_DCC.')

    @field_validator('amount', mode='before')
    @classmethod
    def _blank_amount_to_none(cls, value):
        # Keep the raw integer minor units here; scaling needs the currency and
        # is applied in from_merchant_parameters.
        return None if value in (None, '') else value

    @classmethod
    def from_merchant_parameters(cls, merchant_parameters: bytes) -> 'Response':
        response = cls.model_validate(decode_merchant_parameters(merchant_parameters))
        if response.amount is not None:
            response.amount = response.amount / minor_units_factor(response.currency)
        return response

    def get_order(self) -> str | None:
        return self.order

    @property
    def response_code(self):
        # A 3DS challenge response may carry no Ds_Response. The code is returned
        # as-is; see docs/response-codes.md for the English meanings.
        return int(self.response) if self.response not in (None, '') else None

    def is_paid(self) -> bool:
        return self.response_code is not None and 0 <= self.response_code <= 99

    def is_refunded(self) -> bool:
        return self.response_code == 900

    def is_canceled(self) -> bool:
        return self.response_code == 400

    def is_authorized(self) -> bool:
        return self.is_paid() or self.is_refunded() or self.is_canceled()

    # 3-D Secure (EMV 3DS) accessors over the Ds_EMV3DS response object.
    @property
    def _emv3ds(self) -> dict:
        return self.emv3ds or {}

    @property
    def protocol_version(self):
        return self._emv3ds.get('protocolVersion')

    @property
    def three_ds_server_trans_id(self):
        return self._emv3ds.get('threeDSServerTransID')

    @property
    def three_ds_method_url(self):
        return self._emv3ds.get('threeDSMethodURL')

    @property
    def acs_url(self):
        return self._emv3ds.get('acsURL')

    @property
    def creq(self):
        return self._emv3ds.get('creq')

    def is_no_3ds(self) -> bool:
        return self.protocol_version == 'NO_3DS_V2'

    def requires_challenge(self) -> bool:
        return self._emv3ds.get('threeDSInfo') == 'ChallengeRequest'


__all__ = [
    'BaseRequest',
    'RedirectPaymentMessage',
    'RedirectPreauthorizationMessage',
    'DirectPaymentMessage',
    'DirectPreauthorizationMessage',
    'ConfirmationMessage',
    'RefundMessage',
    'CancellationMessage',
    'Response',
    'decode_merchant_parameters',
    'minor_units_factor',
]
