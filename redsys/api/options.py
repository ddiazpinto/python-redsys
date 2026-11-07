"""Values of request options with a closed set: direct payment, DCC, OTA, financing and PayPal shipping address."""

DIRECT_PAYMENT = 'true'
"""``Ds_Merchant_DirectPayment``: skip authentication; required for MIT, ignored for cards under PSD2."""

MOTO = 'moto'
"""``Ds_Merchant_DirectPayment``: a mail or telephone order (MOTO)."""

DIRECT_PAYMENTS = (DIRECT_PAYMENT, MOTO)

DCC_QUERY = 'Y'
"""``Ds_Merchant_DCC`` on the 3DS initialization: asks for a currency conversion offer."""

NO_DCC_QUERY = 'N'
"""``Ds_Merchant_DCC`` on the 3DS initialization: asks for none."""

DCC_QUERIES = (DCC_QUERY, NO_DCC_QUERY)

OTA_INITIAL = 'S'
"""``Ds_Merchant_OTA``: the initial operation of an online travel agency (OTA) authentication."""

FINANCING_QUERY = 'Y'
"""``Ds_Merchant_Financing`` on the 3DS initialization: asks which financing options apply."""

SHIPPING_ADDRESS = 'S'
"""``Ds_Merchant_ShippingAddressPyP``: the response carries the PayPal account's shipping address."""

NO_SHIPPING_ADDRESS = 'N'
"""``Ds_Merchant_ShippingAddressPyP``: the response leaves the shipping address out."""

SHIPPING_ADDRESS_OPTIONS = (SHIPPING_ADDRESS, NO_SHIPPING_ADDRESS)
