"""Values of ``Ds_SecurePayment`` in responses, as strings."""

NOT_SECURE = '0'
"""Not authenticated."""

ATTEMPT = '1'
"""Authentication attempt: merchant enrolled, cardholder not; Bizum uses it for an authenticated payment."""

SECURE = '2'
"""Authenticated; only with the merchant option for more information, which otherwise reports it as ``1``."""

SECURE_PAYMENTS = (NOT_SECURE, ATTEMPT, SECURE)
