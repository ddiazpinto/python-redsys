AUTHORIZATION = 0
"""Authorization."""

PREAUTHORIZATION = 1
"""Pre-authorization."""

CONFIRMATION = 2
"""Confirmation."""

REFUND = 3
"""Refund."""

AUTHENTICATION = 7
"""Authentication."""

AUTHENTICATION_CONFIRMATION = 8
"""Authentication confirmation"""

CANCELLATION = 9
"""Cancellation"""

REPLACEMENT_PREAUTHORIZATION = 11
"""Replacement preauthorization: extends an existing preauthorization."""

PAY_GOLD = 15
"""Pay gold"""

AUTHENTICATION_PUCE = 17
"""PUCE authentication"""

REFUND_WITHOUT_ORIGINAL = 34
"""Refund without original"""

BETTING_PRICE = 37
"""Betting price"""

PAY_GOLD_AUTHORIZATION = 38
"""PayGold authorization: the cardholder completes a PayGold request (type 15); sent by RedSys, not the merchant."""

DELETE_REFERENCE = 44
"""Delete a stored card reference (token)."""

PAYMENT_CANCELLATION = 45
"""Payment cancellation, for merchant time-outs or technical errors."""

REFUND_CANCELLATION = 46
"""Refund cancellation, within 48 hours of the refund."""

AUTHENTICATION_CONFIRMATION_CANCELLATION = 47
"""Cancellation of an authentication confirmation (type 8)."""

PARTIAL_CONFIRMATION = 48
"""Partial confirmation of a preauthorization."""

TRANSACTION_TYPES = (
    AUTHORIZATION,
    PREAUTHORIZATION,
    CONFIRMATION,
    REFUND,
    AUTHENTICATION,
    AUTHENTICATION_CONFIRMATION,
    CANCELLATION,
    REPLACEMENT_PREAUTHORIZATION,
    PAY_GOLD,
    AUTHENTICATION_PUCE,
    REFUND_WITHOUT_ORIGINAL,
    BETTING_PRICE,
    PAY_GOLD_AUTHORIZATION,
    DELETE_REFERENCE,
    PAYMENT_CANCELLATION,
    REFUND_CANCELLATION,
    AUTHENTICATION_CONFIRMATION_CANCELLATION,
    PARTIAL_CONFIRMATION,
)
