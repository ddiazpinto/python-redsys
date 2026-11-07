"""Named ``Ds_Response`` codes; ``redsys.codes.describe()`` gives their meaning.

Responses carry the code as four digits (``'0195'``); ``Response.response_code`` is the integer.
"""

AUTHORIZED = 0
"""Approved payment or pre-authorization; any code from 0 to 99 means the same."""

CARD_EXPIRED = 101
"""Card expired; do not retry."""

CARD_INVALID = 102
"""Card invalid; do not retry."""

OPERATION_NOT_ALLOWED_FOR_CARD = 104
"""Operation not allowed for this card; ask issuer."""

PIN_ATTEMPTS_EXCEEDED = 106
"""Too many PIN attempts."""

CONTACT_ISSUER = 107
"""Cardholder should contact the issuer."""

AMOUNT_NOT_ALLOWED = 110
"""Amount not allowed for this operation; ask issuer."""

PIN_REQUIRED = 112
"""PIN is required."""

CARD_NOT_VALID_FOR_OPERATION = 114
"""Card cannot be used for this operation; ask issuer."""

CARD_INVALID_115 = 115
"""Card invalid; do not retry."""

INSUFFICIENT_FUNDS = 116
"""Insufficient funds."""

WRONG_PIN = 117
"""Wrong PIN."""

CARD_NOT_REGISTERED = 118
"""Card not registered; do not retry."""

TRANSACTION_LIMIT_EXCEEDED = 121
"""Transaction limit exceeded; ask issuer."""

CARDHOLDER_AUTHENTICATION_FAILED_ASK_ISSUER = 123
"""Cardholder authentication failed; ask issuer."""

CARD_NOT_ACTIVE = 125
"""Card not active for use; do not retry."""

AUTHENTICATION_FORMAT_ERROR = 126
"""Authentication format error; ask issuer."""

WRONG_SECURITY_CODE = 129
"""Wrong security code (CVV2/CVC2)."""

CURRENCY_NOT_SUPPORTED = 130
"""Currency not supported by the issuer."""

UNAUTHENTICATED_LIMIT_EXCEEDED = 162
"""Limit of unauthenticated transactions exceeded."""

CARD_INACTIVE = 163
"""Card inactive."""

CARD_INACTIVE_171 = 171
"""Card inactive."""

DECLINED_DO_NOT_RETRY = 172
"""Declined; brand says never retry."""

DECLINED_UPDATE_CARD_DATA = 173
"""Declined; retry only with updated card data."""

DECLINED_RETRY_AFTER_72_HOURS = 174
"""Declined; wait 72 hours before retrying."""

CARD_NOT_ACCEPTED = 180
"""Card not accepted by this service."""

CARD_DEBIT_RESTRICTED = 181
"""Card has debit restrictions."""

CARD_CREDIT_RESTRICTED = 182
"""Card has credit restrictions."""

CARDHOLDER_AUTHENTICATION_FAILED = 184
"""Cardholder authentication failed."""

AUTHENTICATION_FORMAT_ERROR_187 = 187
"""Authentication format error; ask issuer."""

DECLINED_BY_ISSUER = 190
"""Issuer declined without a stated reason."""

WRONG_EXPIRY_DATE = 191
"""Wrong expiry date."""

AMOUNT_EXCEEDED = 193
"""Amount exceeded."""

SCA_REQUIRED = 195
"""Soft decline: SCA authentication required."""

CARD_INVALID_201 = 201
"""Card invalid; do not retry."""

CARD_BLOCKED_RETAIN = 202
"""Card under temporary block or fraud suspicion; retain."""

OPERATION_NOT_ALLOWED_FOR_CARD_OR_TERMINAL = 204
"""Operation not allowed for this card or terminal."""

PIN_ATTEMPTS_EXCEEDED_DO_NOT_RETRY = 206
"""Too many PIN attempts; do not retry."""

DECLINED = 290
"""Declined without a stated reason."""

UPDATE_OR_QUERY_COMPLETED = 300
"""Update or query completed."""

CANCELLATION_AUTHORIZED = 400
"""Cancellation (void) approved."""

CANCELLATION_AUTHORIZED_LATE = 481
"""Cancellation approved despite excessive delay."""

SIGN_OFF_WITHOUT_SESSION = 881
"""Sign-off message without an open session."""

REFUND_OR_CONFIRMATION_AUTHORIZED = 900
"""Refund or confirmation approved (also PUCE authentication)."""

MERCHANT_NOT_REGISTERED = 904
"""Merchant not registered in FUC."""

SYSTEM_ERROR = 909
"""System error."""

ISSUER_UNAVAILABLE = 912
"""Issuer unavailable."""

DUPLICATE_ORDER = 913
"""Duplicate order."""

ALREADY_CANCELED = 940
"""Transaction already canceled."""

ORIGINAL_AUTHORIZATION_DECLINED = 941
"""Original authorization was declined."""

INVALID_SESSION = 944
"""Wrong session."""

DUPLICATE_SYSTEM_REFERENCE = 945
"""Duplicate system transaction reference."""

REFUND_NOT_ALLOWED = 950
"""Refund not allowed."""

RULES_BREACH = 965
"""Breach of existing rules."""

SENT_FOR_EMV3DS_2_1_AUTHENTICATION = 8210
"""Sent to issuer for EMV3DS 2.1 authentication."""

SENT_FOR_EMV3DS_2_2_AUTHENTICATION = 8220
"""Sent to issuer for EMV3DS 2.2 authentication."""

WRONG_CARD_NUMBER_LENGTH = 9064
"""Card number has the wrong length."""

TRANSACTION_TYPE_NOT_ALLOWED_FOR_CARD = 9078
"""Transaction type not allowed for this card."""

CARD_DOES_NOT_EXIST = 9093
"""Card does not exist."""

REJECTED_BY_INTERNATIONAL_SERVERS = 9094
"""Rejected by international servers."""

CARDHOLDER_WITHOUT_SECURE_KEY = 9104
"""Secure-only merchant, cardholder without secure purchase key."""

SECURE_OPERATIONS_NOT_ALLOWED = 9218
"""Merchant forbids secure operations on this entry."""

CARD_CHECK_DIGIT_FAILED = 9253
"""Card number fails the check digit."""

MERCHANT_CANNOT_PREAUTHORIZE = 9256
"""Merchant cannot make pre-authorizations."""

CARD_CANNOT_PREAUTHORIZE = 9257
"""Card does not allow pre-authorizations."""

ENTRY_RESTRICTION_STOP = 9261
"""Stopped by SIS entry restriction controls."""

CANCELED_BY_USER = 9915
"""Payment canceled by the user."""

CARD_OPERATION_IN_PROGRESS = 9997
"""Another transaction with the same card in progress."""

WAITING_FOR_CARD_DATA = 9998
"""Waiting for card data entry."""

SENT_FOR_AUTHENTICATION = 9999
"""Sent to issuer for authentication."""

RESPONSE_CODES = (
    AUTHORIZED,
    CARD_EXPIRED,
    CARD_INVALID,
    OPERATION_NOT_ALLOWED_FOR_CARD,
    PIN_ATTEMPTS_EXCEEDED,
    CONTACT_ISSUER,
    AMOUNT_NOT_ALLOWED,
    PIN_REQUIRED,
    CARD_NOT_VALID_FOR_OPERATION,
    CARD_INVALID_115,
    INSUFFICIENT_FUNDS,
    WRONG_PIN,
    CARD_NOT_REGISTERED,
    TRANSACTION_LIMIT_EXCEEDED,
    CARDHOLDER_AUTHENTICATION_FAILED_ASK_ISSUER,
    CARD_NOT_ACTIVE,
    AUTHENTICATION_FORMAT_ERROR,
    WRONG_SECURITY_CODE,
    CURRENCY_NOT_SUPPORTED,
    UNAUTHENTICATED_LIMIT_EXCEEDED,
    CARD_INACTIVE,
    CARD_INACTIVE_171,
    DECLINED_DO_NOT_RETRY,
    DECLINED_UPDATE_CARD_DATA,
    DECLINED_RETRY_AFTER_72_HOURS,
    CARD_NOT_ACCEPTED,
    CARD_DEBIT_RESTRICTED,
    CARD_CREDIT_RESTRICTED,
    CARDHOLDER_AUTHENTICATION_FAILED,
    AUTHENTICATION_FORMAT_ERROR_187,
    DECLINED_BY_ISSUER,
    WRONG_EXPIRY_DATE,
    AMOUNT_EXCEEDED,
    SCA_REQUIRED,
    CARD_INVALID_201,
    CARD_BLOCKED_RETAIN,
    OPERATION_NOT_ALLOWED_FOR_CARD_OR_TERMINAL,
    PIN_ATTEMPTS_EXCEEDED_DO_NOT_RETRY,
    DECLINED,
    UPDATE_OR_QUERY_COMPLETED,
    CANCELLATION_AUTHORIZED,
    CANCELLATION_AUTHORIZED_LATE,
    SIGN_OFF_WITHOUT_SESSION,
    REFUND_OR_CONFIRMATION_AUTHORIZED,
    MERCHANT_NOT_REGISTERED,
    SYSTEM_ERROR,
    ISSUER_UNAVAILABLE,
    DUPLICATE_ORDER,
    ALREADY_CANCELED,
    ORIGINAL_AUTHORIZATION_DECLINED,
    INVALID_SESSION,
    DUPLICATE_SYSTEM_REFERENCE,
    REFUND_NOT_ALLOWED,
    RULES_BREACH,
    SENT_FOR_EMV3DS_2_1_AUTHENTICATION,
    SENT_FOR_EMV3DS_2_2_AUTHENTICATION,
    WRONG_CARD_NUMBER_LENGTH,
    TRANSACTION_TYPE_NOT_ALLOWED_FOR_CARD,
    CARD_DOES_NOT_EXIST,
    REJECTED_BY_INTERNATIONAL_SERVERS,
    CARDHOLDER_WITHOUT_SECURE_KEY,
    SECURE_OPERATIONS_NOT_ALLOWED,
    CARD_CHECK_DIGIT_FAILED,
    MERCHANT_CANNOT_PREAUTHORIZE,
    CARD_CANNOT_PREAUTHORIZE,
    ENTRY_RESTRICTION_STOP,
    CANCELED_BY_USER,
    CARD_OPERATION_IN_PROGRESS,
    WAITING_FOR_CARD_DATA,
    SENT_FOR_AUTHENTICATION,
)
