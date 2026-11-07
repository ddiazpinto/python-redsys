"""Values of request options with a closed set: OTA, financing and the PayPal shipping address."""

OTA_INITIAL = 'S'
"""``Ds_Merchant_OTA``: the initial operation of an online travel agency (OTA) authentication."""

FINANCING_QUERY = 'Y'
"""``Ds_Merchant_Financing`` on the 3DS initialization: asks which financing options apply."""

SHIPPING_ADDRESS = 'S'
"""``Ds_Merchant_ShippingAddressPyP``: the response carries the PayPal account's shipping address."""

NO_SHIPPING_ADDRESS = 'N'
"""``Ds_Merchant_ShippingAddressPyP``: the response leaves the shipping address out."""

SHIPPING_ADDRESS_OPTIONS = (SHIPPING_ADDRESS, NO_SHIPPING_ADDRESS)
