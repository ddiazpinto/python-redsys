# Migrating from 1.x to 2.x

2.0 changes the API. The 1.x line receives fixes until 2026-12-31; pin `python-redsys>=1.2,<2` until the migration is done.

## Requirements

Python 3.10 or later. `cryptography` and `pydantic` replace `pycryptodome`. The default signature version is `HMAC_SHA512_V2`; `signature_version=HMAC_SHA256_V1` on the client keeps the 1.x scheme during the transition.

## Building a request

```python
# 1.x
from redsys.client import RedirectClient
from redsys.constants import EUR, STANDARD_PAYMENT

client = RedirectClient(secret_key="...")
fields = client.prepare_request({
    "merchant_code": "999008881", "terminal": "1",
    "transaction_type": STANDARD_PAYMENT, "currency": EUR,
    "order": "000000000001", "amount": Decimal("10.56"),
    "merchant_url": "https://example.com/notify",
})

# 2.x
from redsys import currencies
from redsys.clients import RedirectClient

client = RedirectClient(secret_key="...", merchant_code="999008881", terminal=1)
fields = client.payment(
    order="000000000001", amount=Decimal("10.56"), currency=currencies.EUR,
    merchant_url="https://example.com/notify",
).to_dict()
```

- `merchant_code` and `terminal` (an integer) move to the constructor. `sandbox=True` selects the test endpoint, exposed as `client.endpoint`.
- The method chooses the operation: `payment()` and `preauthorization()`, plus `confirmation()`, `refund()` and `cancellation()` on the direct clients. Other types go through `client.request(transaction_type, ...)`.
- `to_dict()` returns `str` values; the `.decode()` before rendering the form is no longer needed.
- `payment_method` is now `pay_methods` and `mobile_number` is `bizum_mobile_number`; `transaction_date` has no equivalent. A 1.x name raises `ValidationError` naming its replacement.
- `redsys.constants` splits into `currencies`, `languages` and `transactions` (`from redsys import ...`). Transaction types and languages are integers: `STANDARD_PAYMENT` is `transactions.AUTHORIZATION`, `"001"` is `languages.SPANISH`. Types 5, 6, O, P, Q, R and S have no 2.x equivalent.
- `order` accepts 4 to 12 characters; 1.x required exactly 12.

## Reading a response

```python
# 1.x
response = client.create_response(signature, merchant_parameters)
if response.is_paid:
    ...

# 2.x
response = client.parse_response(received)  # the Ds_* fields RedSys posted back
if response.is_paid():
    ...
```

- Predicates are methods. `response.is_paid` without parentheses is always truthy.
- `response.code` is `response.response_code`. `response.message` is gone; meanings are in [`response-codes.md`](response-codes.md).
- `response.parameters` is `response.model_dump()`; unlisted parameters are in `response.model_extra`. `merchant_cof_txnid` is `cof_txnid`.
- A signature mismatch still raises `ValueError`. A RedSys error payload raises `redsys.exceptions.ResponseError`.
