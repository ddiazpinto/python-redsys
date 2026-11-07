"""ISO 4217 numeric codes for ``Ds_Merchant_Currency``."""

EUR = 978
"""Euro."""

USD = 840
"""United States dollar."""

GBP = 826
"""Pound sterling."""

JPY = 392
"""Japanese yen."""

ARS = 32
"""Argentine peso."""

CAD = 124
"""Canadian dollar."""

CLP = 152
"""Chilean peso."""

COP = 170
"""Colombian peso."""

INR = 356
"""Indian rupee."""

MXN = 484
"""Mexican peso."""

PEN = 604
"""Peruvian sol."""

CHF = 756
"""Swiss franc."""

BRL = 986
"""Brazilian real."""

VEF = 937
"""Venezuelan bolivar."""

TRY = 949
"""Turkish lira."""

CURRENCIES = (
    EUR,
    USD,
    GBP,
    JPY,
    ARS,
    CAD,
    CLP,
    COP,
    INR,
    MXN,
    PEN,
    CHF,
    BRL,
    VEF,
    TRY,
)


# ISO 4217 minor-unit exponent: the decimals of ``amount`` on the wire; 2 for a currency not listed.
CURRENCY_DECIMALS = {
    EUR: 2,
    USD: 2,
    GBP: 2,
    JPY: 0,
    ARS: 2,
    CAD: 2,
    CLP: 0,
    COP: 2,
    INR: 2,
    MXN: 2,
    PEN: 2,
    CHF: 2,
    BRL: 2,
    VEF: 2,
    TRY: 2,
}
