# -*- coding: utf-8 -*-
from decimal import Decimal

RESPONSE = 'Ds_Response'
DATE = 'Ds_Date'
HOUR = 'Ds_Hour'
MERCHANT_CODE = 'Ds_MerchantCode'
TERMINAL = 'Ds_Terminal'
TRANSACTION_TYPE = 'Ds_TransactionType'
ORDER = 'Ds_Order'
CURRENCY = 'Ds_Currency'
AMOUNT = 'Ds_Amount'
MERCHANT_DATA = 'Ds_MerchantData'
CONSUMER_LANGUAGE = 'Ds_ConsumerLanguage'
CARD_COUNTRY = 'Ds_Card_Country'
CARD_TYPE = 'Ds_Card_Type'
CARD_BRAND = 'Ds_Card_Brand'
SECURE_PAYMENT = 'Ds_SecurePayment'
AUTHORIZATION_CODE = 'Ds_AuthorisationCode'
COF_TXNID = 'Ds_Merchant_Cof_Txnid'
ERROR_CODE = 'Ds_ErrorCode'

RESPONSE_MAP = {
    '0000': 'Transacción autorizada para pagos y preautorizaciones',
    '0900': 'Transacción autorizada para devoluciones y confirmaciones',
    '0400': 'Transacción autorizada para anulaciones',
    '0101': 'Tarjeta caducada',
    '0102': 'Tarjeta en excepción transitoria o bajo sospecha de fraude',
    '0106': 'Intentos de PIN excedidos',
    '0125': 'Tarjeta no efectiva',
    '0129': 'Código de seguridad (CVV2/CVC2) incorrecto',
    '0180': 'Tarjeta ajena al servicio',
    '0184': 'Error en la autenticación del titular',
    '0190': 'Denegación del emisor sin especificar motivo',
    '0191': 'Fecha de caducidad errónea',
    '0202': 'Tarjeta en excepción transitoria o bajo sospecha de fraude con retirada de tarjeta',
    '0904': 'Comercio no registrado en FUC',
    '0909': 'Error de sistema',
    '0912': 'Emisor no disponible',
    '0913': 'Pedido repetido',
    '0944': 'Sesión Incorrecta',
    '0950': 'Operación de devolución no permitida',
    '9912': 'Emisor no disponible',
    '9064': 'Número de posiciones de la tarjeta incorrecto',
    '9078': 'Tipo de operación no permitida para esa tarjeta',
    '9093': 'Tarjeta no existente',
    '9094': 'Rechazo servidores internacionales',
    '9104': 'Comercio con “titular seguro” y titular sin clave de compra segura',
    '9218': 'El comercio no permite op. seguras por entrada /operaciones',
    '9253': 'Tarjeta no cumple el check-digit',
    '9256': 'El comercio no puede realizar preautorizaciones',
    '9257': 'Esta tarjeta no permite operativa de preautorizaciones',
    '9261': 'Operación detenida por superar el control de restricciones en la entrada al SIS',
    '9913': 'Error en la confirmación que el comercio envía al TPV Virtual',
    '9914': 'Confirmación “KO” del comercio',
    '9915': 'A petición del usuario se ha cancelado el pago',
    '9928': 'Anulación de autorización en diferido realizada por el SIS (proceso batch)',
    '9929': 'Anulación de autorización en diferido realizada por el comercio',
    '9997': 'Se está procesando otra transacción en SIS con la misma tarjeta',
    '9998': 'Operación en proceso de solicitud de datos de tarjeta',
    '9999': 'Operación que ha sido redirigida al emisor a autenticar',
}

MERCHANT_PARAMETERS_MAP = {
    'response': RESPONSE,
    'date': DATE,
    'hour': HOUR,
    'merchant_code': MERCHANT_CODE,
    'terminal': TERMINAL,
    'transaction_type': TRANSACTION_TYPE,
    'order': ORDER,
    'currency': CURRENCY,
    'amount': AMOUNT,
    'merchant_data': MERCHANT_DATA,
    'consumer_language': CONSUMER_LANGUAGE,
    'card_country': CARD_COUNTRY,
    'card_type': CARD_TYPE,
    'card_brand': CARD_BRAND,
    'secure_payment': SECURE_PAYMENT,
    'authorization_code': AUTHORIZATION_CODE,
    'cof_txnid': COF_TXNID,
    'error_code': ERROR_CODE,
}


class Response(object):
    """
    Defines a response
    """
    _parameters = {}

    def __init__(self, parameters):
        MERCHANT_PARAMETERS_MAP_REVERSE = {value: key for key, value in MERCHANT_PARAMETERS_MAP.items()}
        for key, value in parameters.items():
            clean = getattr(self, "clean_%s" % MERCHANT_PARAMETERS_MAP_REVERSE[key], None)
            self._parameters[MERCHANT_PARAMETERS_MAP_REVERSE[key]] = clean(value) if clean else value

    def __getattr__(self, item):
        if item in MERCHANT_PARAMETERS_MAP:
            return self._parameters[item]

    def __setattr__(self, key, value):
        if key in MERCHANT_PARAMETERS_MAP:
            self._parameters[key] = value

    def is_authorized(self):
        return (0 <= self.response_code <= 99) or self.response_code == 900 or self.response_code == 400

    def is_paid(self):
        return 0 <= self.response_code <= 99

    def is_refunded(self):
        return self.response_code == 900

    def is_canceled(self):
        return self.response_code == 400

    @property
    def response_code(self):
        return int(self.response)

    @property
    def response_message(self):
        return RESPONSE_MAP['0000'] if self.is_paid() else RESPONSE_MAP[self.response]

    def clean_amount(self, value):
        return Decimal("%s.%s" % (str(value)[:-2], str(value)[-2:]))
