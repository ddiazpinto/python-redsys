"""Google Pay and Apple Pay values for ``DS_XPAYTYPE``, ``DS_XPAYORIGEN`` and ``DS_XPAYDECODEDDATA``."""

GOOGLE = 'Google'
"""``DS_XPAYTYPE``: Google Pay."""

APPLE = 'Apple'
"""``DS_XPAYTYPE``: Apple Pay."""

TYPES = (GOOGLE, APPLE)

WEB = 'WEB'
"""``DS_XPAYORIGEN``: the wallet was used on a website."""

IN_APP = 'InApp'
"""``DS_XPAYORIGEN``: the wallet was used in a mobile app."""

ORIGINS = (WEB, IN_APP)

CARD = 'CARD'
"""``paymentMethod`` in ``DS_XPAYDECODEDDATA`` (Google Pay): a card without cryptogram."""

TOKENIZED_CARD = 'TOKENIZED_CARD'
"""``paymentMethod`` in ``DS_XPAYDECODEDDATA`` (Google Pay): a tokenized card with cryptogram."""

PAYMENT_METHODS = (CARD, TOKENIZED_CARD)
