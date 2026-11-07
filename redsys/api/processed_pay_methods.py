"""Values of ``Ds_ProcessedPayMethod``: the method an operation was processed with, as strings.

RedSys may add values; compare against these without rejecting others.
"""

VISA_SECURE = '1'
"""Visa Secure."""

TRADITIONAL_WORLDWIDE = '3'
"""Traditional payment, worldwide."""

FINANET = '5'
"""Finanet."""

FINANET_CAPABLE = '11'
"""Finanet capable."""

VISA_SECURE_CAPABLE = '13'
"""Visa Secure capable."""

TRADITIONAL_EU = '14'
"""Traditional payment, European Union."""

MASTERCARD_IDENTITY_CHECK = '22'
"""Mastercard Identity Check."""

IDENTITY_CHECK_CAPABLE = '23'
"""Identity Check capable."""

AMEX = '24'
"""American Express payment."""

MOTO = '25'
"""Mail or telephone order (MOTO) payment."""

JCB = '28'
"""JCB payment."""

DINERS = '31'
"""Diners payment."""

JCB_J_SECURE = '39'
"""JCB J/Secure."""

J_SECURE_CAPABLE = '40'
"""J/Secure capable."""

DIRECT_DEBIT = '41'
"""Direct debit."""

BANK_TRANSFER = '42'
"""Bank transfer."""

PAYPAL = '54'
"""PayPal."""

AMEX_SAFEKEY = '57'
"""American Express SafeKey."""

SAFEKEY_CAPABLE = '58'
"""SafeKey capable."""

MASTERPASS = '59'
"""Masterpass wallet."""

BIZUM = '68'
"""Bizum."""

UPI_EXPRESSPAY = '70'
"""UPI ExpressPay."""

GOOGLE_PAY = '71'
"""Google Pay."""

APPLE_PAY = '72'
"""Apple Pay."""

UPI_SECUREPLUS = '73'
"""UPI SecurePlus."""

DISCOVER_CAPABLE = '74'
"""Discover capable."""

DISCOVER_PROTECTBUY = '75'
"""Discover ProtectBuy."""

DISCOVER = '76'
"""Discover."""

AMAZON_PAY = '77'
"""Amazon Pay."""

VISA_CHALLENGE = '78'
"""Visa, with challenge."""

MASTERCARD_CHALLENGE = '79'
"""Mastercard, with challenge."""

VISA_FRICTIONLESS = '80'
"""Visa, frictionless."""

MASTERCARD_FRICTIONLESS = '81'
"""Mastercard, frictionless."""

VISA_ATTEMPT = '82'
"""Visa, authentication attempt."""

MASTERCARD_ATTEMPT = '83'
"""Mastercard, authentication attempt."""

AMEX_CHALLENGE = '85'
"""American Express, with challenge."""

DISCOVER_CHALLENGE = '86'
"""Discover, with challenge."""

AMEX_FRICTIONLESS = '87'
"""American Express, frictionless."""

DISCOVER_FRICTIONLESS = '88'
"""Discover, frictionless."""

AMEX_ATTEMPT = '89'
"""American Express, authentication attempt."""

DISCOVER_ATTEMPT = '90'
"""Discover, authentication attempt."""

DINERS_PROTECTBUY = '92'
"""Diners ProtectBuy payment."""

DINERS_PROTECTBUY_CHALLENGE = '93'
"""Diners ProtectBuy, with challenge."""

DINERS_PROTECTBUY_FRICTIONLESS = '94'
"""Diners ProtectBuy, frictionless."""

DINERS_PROTECTBUY_ATTEMPT = '95'
"""Diners ProtectBuy, authentication attempt."""

JCB_CHALLENGE = '96'
"""JCB, with challenge."""

JCB_FRICTIONLESS = '97'
"""JCB, frictionless."""

JCB_ATTEMPT = '98'
"""JCB, authentication attempt."""

SAMSUNG_PAY = '106'
"""Samsung Pay."""

PAY_BY_ACCOUNT = '107'
"""Pay by account."""

PROCESSED_PAY_METHODS = (
    VISA_SECURE,
    TRADITIONAL_WORLDWIDE,
    FINANET,
    FINANET_CAPABLE,
    VISA_SECURE_CAPABLE,
    TRADITIONAL_EU,
    MASTERCARD_IDENTITY_CHECK,
    IDENTITY_CHECK_CAPABLE,
    AMEX,
    MOTO,
    JCB,
    DINERS,
    JCB_J_SECURE,
    J_SECURE_CAPABLE,
    DIRECT_DEBIT,
    BANK_TRANSFER,
    PAYPAL,
    AMEX_SAFEKEY,
    SAFEKEY_CAPABLE,
    MASTERPASS,
    BIZUM,
    UPI_EXPRESSPAY,
    GOOGLE_PAY,
    APPLE_PAY,
    UPI_SECUREPLUS,
    DISCOVER_CAPABLE,
    DISCOVER_PROTECTBUY,
    DISCOVER,
    AMAZON_PAY,
    VISA_CHALLENGE,
    MASTERCARD_CHALLENGE,
    VISA_FRICTIONLESS,
    MASTERCARD_FRICTIONLESS,
    VISA_ATTEMPT,
    MASTERCARD_ATTEMPT,
    AMEX_CHALLENGE,
    DISCOVER_CHALLENGE,
    AMEX_FRICTIONLESS,
    DISCOVER_FRICTIONLESS,
    AMEX_ATTEMPT,
    DISCOVER_ATTEMPT,
    DINERS_PROTECTBUY,
    DINERS_PROTECTBUY_CHALLENGE,
    DINERS_PROTECTBUY_FRICTIONLESS,
    DINERS_PROTECTBUY_ATTEMPT,
    JCB_CHALLENGE,
    JCB_FRICTIONLESS,
    JCB_ATTEMPT,
    SAMSUNG_PAY,
    PAY_BY_ACCOUNT,
)
