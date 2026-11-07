"""Values of ``Ds_Merchant_PayMethods``: the payment methods offered on the RedSys payment page.

RedSys publishes no closed table; these are the values its guides use. On a PayGold link
several letters can go together (for example ``CzP``).
"""

BIZUM = 'z'
"""Bizum (Bizum guide 2.6, PayGold guide 1.8.2)."""

CARD = 'C'
"""Card only (PayGold guide 1.8.2)."""

BANK_TRANSFER = 'R'
"""Bank transfer (PayGold guide 1.8.2)."""

PAYPAL = 'P'
"""PayPal (PayGold guide 1.8.2)."""

XPAY = 'xpay'
"""Only the Google Pay and Apple Pay buttons (Google Pay guide 1.9, Apple Pay guide 3.2)."""

GOOGLE_PAY = 'google'
"""Straight to Google Pay (Google Pay guide 1.9)."""

PAY_METHODS = (BIZUM, CARD, BANK_TRANSFER, PAYPAL, XPAY, GOOGLE_PAY)
