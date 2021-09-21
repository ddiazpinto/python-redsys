from decimal import Decimal
from typing import Any, Dict

RESPONSE = "Ds_Response"
DATE = "Ds_Date"
HOUR = "Ds_Hour"
MERCHANT_CODE = "Ds_MerchantCode"
TERMINAL = "Ds_Terminal"
TRANSACTION_TYPE = "Ds_TransactionType"
ORDER = "Ds_Order"
CURRENCY = "Ds_Currency"
AMOUNT = "Ds_Amount"
MERCHANT_DATA = "Ds_MerchantData"
CONSUMER_LANGUAGE = "Ds_ConsumerLanguage"
CARD_COUNTRY = "Ds_Card_Country"
CARD_TYPE = "Ds_Card_Type"
CARD_BRAND = "Ds_Card_Brand"
MERCHANT_COF_TXNID = "Ds_Merchant_Cof_Txnid"
SECURE_PAYMENT = "Ds_SecurePayment"
AUTHORIZATION_CODE = "Ds_AuthorisationCode"
ERROR_CODE = "Ds_ErrorCode"
AMOUNT_EURO = "Ds_Amount_Euro"
PROCESSED_PAY_METHOD = "Ds_ProcessedPayMethod"

RESPONSE_MAP = {
    "0000": "Transacción autorizada para pagos y preautorizaciones",
    "900": "Transacción autorizada para devoluciones y confirmaciones",
    "400": "Transacción autorizada para anulaciones",
    "101": "Tarjeta caducada",
    "102": "Tarjeta en excepción transitoria o bajo sospecha de fraude",
    "106": "Intentos de PIN excedidos",
    "125": "Tarjeta no efectiva",
    "129": "Código de seguridad (CVV2/CVC2) incorrecto",
    "180": "Tarjeta ajena al servicio",
    "184": "Error en la autenticación del titular",
    "190": "Denegación del emisor sin especificar motivo",
    "191": "Fecha de caducidad errónea",
    "202": "Tarjeta en excepción transitoria o bajo sospecha de fraude con retirada de tarjeta",
    "904": "Comercio no registrado en FUC",
    "909": "Error de sistema",
    "912": "Emisor no disponible",
    "913": "Pedido repetido",
    "944": "Sesión Incorrecta",
    "950": "Operación de devolución no permitida",
    "9912": "Emisor no disponible",
    "9064": "Número de posiciones de la tarjeta incorrecto",
    "9078": "Tipo de operación no permitida para esa tarjeta",
    "9093": "Tarjeta no existente",
    "9094": "Rechazo servidores internacionales",
    "9104": "Comercio con “titular seguro” y titular sin clave de compra segura",
    "9218": "El comercio no permite op. seguras por entrada /operaciones",
    "9253": "Tarjeta no cumple el check-digit",
    "9256": "El comercio no puede realizar preautorizaciones",
    "9257": "Esta tarjeta no permite operativa de preautorizaciones",
    "9261": "Operación detenida por superar el control de restricciones en la entrada al SIS",
    "9913": "Error en la confirmación que el comercio envía al TPV Virtual",
    "9914": "Confirmación “KO” del comercio",
    "9915": "A petición del usuario se ha cancelado el pago",
    "9928": "Anulación de autorización en diferido realizada por el SIS (proceso batch)",
    "9929": "Anulación de autorización en diferido realizada por el comercio",
    "9997": "Se está procesando otra transacción en SIS con la misma tarjeta",
    "9998": "Operación en proceso de solicitud de datos de tarjeta",
    "9999": "Operación que ha sido redirigida al emisor a autenticar",
}

MERCHANT_PARAMETERS_MAP = {
    "response": RESPONSE,
    "date": DATE,
    "hour": HOUR,
    "merchant_code": MERCHANT_CODE,
    "terminal": TERMINAL,
    "transaction_type": TRANSACTION_TYPE,
    "order": ORDER,
    "currency": CURRENCY,
    "amount": AMOUNT,
    "merchant_data": MERCHANT_DATA,
    "consumer_language": CONSUMER_LANGUAGE,
    "card_country": CARD_COUNTRY,
    "card_type": CARD_TYPE,
    "card_brand": CARD_BRAND,
    "merchant_cof_txnid": MERCHANT_COF_TXNID,
    "secure_payment": SECURE_PAYMENT,
    "authorization_code": AUTHORIZATION_CODE,
    "error_code": ERROR_CODE,
    "amount_euro": AMOUNT_EURO,
    "processed_pay_method": PROCESSED_PAY_METHOD,
}


class Response:
    """
    Defines a response
    """

    _parameters: Dict[str, Any] = {}

    def __init__(self, parameters: Dict[str, Any]):
        MERCHANT_PARAMETERS_MAP_REVERSE = {
            value: key for key, value in MERCHANT_PARAMETERS_MAP.items()
        }
        for key, value in parameters.items():
            clean = getattr(
                self, "clean_%s" % MERCHANT_PARAMETERS_MAP_REVERSE[key], None
            )
            self._parameters[MERCHANT_PARAMETERS_MAP_REVERSE[key]] = (
                clean(value) if clean else value
            )

    def __getattr__(self, item: str) -> Any:
        if item in MERCHANT_PARAMETERS_MAP:
            return self._parameters[item]

    def __setattr__(self, key: str, value: Any):
        if key in MERCHANT_PARAMETERS_MAP:
            clean = getattr(self, "clean_%s" % MERCHANT_PARAMETERS_MAP[key], None)
            self._parameters[MERCHANT_PARAMETERS_MAP[key]] = (
                clean(value) if clean else value
            )

    @property
    def is_authorized(self):
        return (0 <= self.code <= 99) or self.code == 900 or self.code == 400

    @property
    def is_paid(self):
        return 0 <= self.code <= 99

    @property
    def is_refunded(self):
        return self.code == 900

    @property
    def is_canceled(self):
        return self.code == 400

    @property
    def code(self):
        return int(self.response)

    @property
    def message(self):
        return RESPONSE_MAP["0000"] if self.is_paid else RESPONSE_MAP[self.response]

    @staticmethod
    def clean_amount(value):
        return Decimal("%s.%s" % (str(value)[:-2], str(value)[-2:]))
