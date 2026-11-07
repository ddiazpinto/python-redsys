import os
import re
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redsys import generate_order, pay_methods
from redsys.models import RedirectPaymentMessage


def _message(order, **fields):
    return RedirectPaymentMessage(merchant_code='999008881', terminal=1, order=order, amount=Decimal('1.00'), **fields)


def test_default_order_has_12_characters_and_4_leading_digits():
    order = generate_order()
    assert len(order) == 12
    assert re.fullmatch(r'[0-9]{4}[a-zA-Z0-9]{8}', order)


@pytest.mark.parametrize('length', range(4, 13))
def test_every_draw_is_a_valid_order(length):
    for _ in range(300):
        order = generate_order(length)
        assert len(order) == length
        assert _message(order).order == order


def test_draws_differ():
    assert len({generate_order() for _ in range(1000)}) == 1000


def test_draws_use_letters_after_the_digits():
    tails = ''.join(generate_order()[4:] for _ in range(200))
    assert re.search('[a-z]', tails) and re.search('[A-Z]', tails) and re.search('[0-9]', tails)


@pytest.mark.parametrize('length', [3, 13, 0, -1, '12', 12.0, True, None])
def test_length_outside_4_to_12_raises(length):
    with pytest.raises(ValueError):
        generate_order(length)


def test_pay_methods():
    assert pay_methods.PAY_METHODS == ('z', 'C', 'R', 'P', 'xpay', 'google')
    params = _message(generate_order(), pay_methods=pay_methods.BIZUM).prepare_parameters()
    assert params['Ds_Merchant_PayMethods'] == 'z'
