"""PSD2 strong customer authentication (SCA) exemption codes for Ds_Merchant_Excep_SCA (REST guide 4.0.1)."""

LWV = 'LWV'
"""Low-value transaction: up to 30 EUR, with issuer-side counters (5 operations or 100 EUR accumulated)."""

TRA = 'TRA'
"""Transaction risk analysis performed by the acquirer or the merchant."""

MIT = 'MIT'
"""Merchant-initiated transaction, no cardholder interaction (stored credentials, subscriptions).

Sent together with direct_payment "true"."""

COR = 'COR'
"""Secure corporate payment, business-to-business only."""

ATD = 'ATD'
"""Delegated authentication, a card-scheme program."""

EXEMPTIONS = (LWV, TRA, MIT, COR, ATD)

QUERY = 'Y'
"""Sent on the 3DS initialization to ask which exemptions the card allows; the answer comes back in Ds_Excep_SCA."""
