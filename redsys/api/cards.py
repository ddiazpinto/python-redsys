"""Card values in responses: ``Ds_Card_Type``, ``Ds_Card_Brand`` and ``Ds_Card_PSD2``.

Strings, as the response fields carry them.
"""

CREDIT = 'C'
"""``Ds_Card_Type``: credit card."""

DEBIT = 'D'
"""``Ds_Card_Type``: debit card."""

VOUCHER = 'V'
"""``Ds_Card_Type``: prepaid voucher."""

MIXED = 'X'
"""``Ds_Card_Type``: mixed card."""

CARD_TYPES = (CREDIT, DEBIT, VOUCHER, MIXED)

VISA = '1'
"""``Ds_Card_Brand``: Visa."""

MASTERCARD = '2'
"""``Ds_Card_Brand``: Mastercard."""

DINERS = '6'
"""``Ds_Card_Brand``: Diners."""

PRIVATE_LABEL = '7'
"""``Ds_Card_Brand``: private label card."""

AMEX = '8'
"""``Ds_Card_Brand``: American Express."""

JCB = '9'
"""``Ds_Card_Brand``: JCB."""

UPI = '22'
"""``Ds_Card_Brand``: UnionPay (UPI, also listed as CUP)."""

BRANDS = (VISA, MASTERCARD, DINERS, PRIVATE_LABEL, AMEX, JCB, UPI)
"""The documented brands; RedSys may return others."""

PSD2 = 'Y'
"""``Ds_Card_PSD2``: the card falls under PSD2 strong customer authentication."""

NOT_PSD2 = 'N'
"""``Ds_Card_PSD2``: it does not."""

PSD2_VALUES = (PSD2, NOT_PSD2)
