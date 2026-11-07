"""PayGold (payment by link) values: SMS placeholders and e-mail XML tags.

The link is created with ``pay_gold()`` (type 15) and its expiry changed with
``pay_gold_expiry_change()`` (type 51).
"""

SMS_MERCHANT = '@COMERCIO@'
"""Placeholder in ``customer_sms_text`` for the merchant name."""

SMS_AMOUNT = '@IMPORTE@'
"""Placeholder in ``customer_sms_text`` for the amount."""

SMS_CURRENCY = '@MONEDA@'
"""Placeholder in ``customer_sms_text`` for the currency."""

SMS_URL = '@URL@'
"""Placeholder in ``customer_sms_text`` for the payment link; required."""

SMS_PLACEHOLDERS = (SMS_MERCHANT, SMS_AMOUNT, SMS_CURRENCY, SMS_URL)

XML_BUYER_NAME = 'nombreComprador'
"""Tag in ``p2f_xml_data`` for the buyer's name."""

XML_BUYER_ADDRESS = 'direccionComprador'
"""Tag in ``p2f_xml_data`` for the buyer's address (parameters table)."""

XML_FREE_TEXT = 'textoLibre1'
"""Tag in ``p2f_xml_data`` for the purchase description."""

XML_MAIL_SUBJECT = 'subjectMailCliente'
"""Tag in ``p2f_xml_data`` for the e-mail subject (PayGold guide example)."""

XML_TAGS = (XML_BUYER_NAME, XML_BUYER_ADDRESS, XML_FREE_TEXT, XML_MAIL_SUBJECT)
