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

PAY_GOLD = 15
"""Pay gold"""

AUTHENTICATION_PUCE = 17
"""PUCE authentication"""

REFUND_WITHOUT_ORIGINAL = 34
"""Refund without original"""

BETTING_PRICE = 37
"""Betting price"""

TRANSACTION_TYPES = (
    AUTHORIZATION,
    PREAUTHORIZATION,
    CONFIRMATION,
    REFUND,
    AUTHENTICATION,
    AUTHENTICATION_CONFIRMATION,
    CANCELLATION,
    PAY_GOLD,
    AUTHENTICATION_PUCE,
    REFUND_WITHOUT_ORIGINAL,
    BETTING_PRICE,
)
