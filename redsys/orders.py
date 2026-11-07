"""Order numbers for ``Ds_Merchant_Order``."""

from secrets import choice
from string import ascii_letters, digits

_ALPHANUMERIC = ascii_letters + digits


def generate_order(length: int = 12) -> str:
    """A random order number of ``length`` characters (4 to 12): 4 digits, then letters and digits.

    RedSys recommends the 4 leading digits. A random draw makes a repeated order (SIS0051)
    unlikely, not impossible. Raises ``ValueError`` for a length outside 4 to 12.
    """
    if isinstance(length, bool) or not isinstance(length, int) or not 4 <= length <= 12:
        raise ValueError('length must be an integer from 4 to 12.')
    return ''.join(choice(digits) for _ in range(4)) + ''.join(choice(_ALPHANUMERIC) for _ in range(length - 4))


__all__ = ['generate_order']
