"""Bizum Request-to-Pay values: ``Ds_RtpStatus`` and the ``Ds_RtpResponse`` codes.

``redsys.codes.describe()`` gives the meaning of each code.
"""

RTP_OK = 'OK'
"""``Ds_RtpStatus``: the customer can receive a payment request, or the backup step succeeded."""

RTP_KO = 'KO'
"""``Ds_RtpStatus``: it cannot or did not; ``Ds_RtpResponse`` says why."""

RTP_STATUSES = (RTP_OK, RTP_KO)

REQUEST_PROCESSED = 'BIZ00000'
"""Request processed successfully."""

MISSING_PARAMETER = 'BIZ00001'
"""A required input parameter is missing."""

INVALID_PARAMETER_FORMAT = 'BIZ00002'
"""An input parameter has an invalid format."""

NOT_FOUND = 'BIZ00003'
"""The requested item was not found."""

INTERNAL_FAILURE = 'BIZ00005'
"""Internal system failure."""

SECURITY_CHECK_FAILED = 'BIZ00006'
"""Security check failed (3DES / MAC X9.19)."""

OPERATION_NOT_ALLOWED = 'BIZ00007'
"""Operation not allowed."""

PAYEE_NOT_FOUND = 'BIZ00008'
"""Payee not found."""

PAYER_NOT_FOUND = 'BIZ00009'
"""Payer not found (customer has no Bizum)."""

FEATURE_NOT_AVAILABLE = 'BIZ00202'
"""Feature not implemented yet (seen when the customer lacks RTP)."""

REQUEST_AUTHENTICATION_FAILED = 'BIZ00213'
"""Authentication of the incoming request failed (security sequence)."""

ISSUER_REJECTED_RTP_AUTHENTICATION = 'BIZ00224'
"""Issuer answered KO to the RTP authentication."""

RTP_AUTHENTICATION_FAILED = 'BIZ00225'
"""RTP authentication did not complete successfully."""

BACKUP_AVAILABLE = 'BIZ00233'
"""Authentication failed but the operation can be backed up (respaldo)."""

RTP_RESPONSES = (
    REQUEST_PROCESSED,
    MISSING_PARAMETER,
    INVALID_PARAMETER_FORMAT,
    NOT_FOUND,
    INTERNAL_FAILURE,
    SECURITY_CHECK_FAILED,
    OPERATION_NOT_ALLOWED,
    PAYEE_NOT_FOUND,
    PAYER_NOT_FOUND,
    FEATURE_NOT_AVAILABLE,
    REQUEST_AUTHENTICATION_FAILED,
    ISSUER_REJECTED_RTP_AUTHENTICATION,
    RTP_AUTHENTICATION_FAILED,
    BACKUP_AVAILABLE,
)
