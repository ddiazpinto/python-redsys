# Welcome to python-redsys!

[![CI](https://github.com/ddiazpinto/python-redsys/actions/workflows/python-app.yml/badge.svg?branch=release/1.x)](https://github.com/ddiazpinto/python-redsys/actions/workflows/python-app.yml?query=branch%3Arelease%2F1.x) [![PyPI](https://img.shields.io/pypi/v/python-redsys.svg)](https://pypi.org/project/python-redsys/) ![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ddiazpinto/python-redsys/blob/release/1.x/LICENSE)

A simple, lightweight client to handle payments through the RedSys platform, using its *redirect connection* (browser form POST).

The library only builds the signed request and verifies/parses the response. It makes no network or browser calls of its own: the payment form is submitted from the cardholder's browser.

## Installation

```bash
pip install "python-redsys>=1.2,<2"

# or with Poetry
poetry add "python-redsys@^1.2"
```

Requires Python 3.8+. Runtime dependency: `pycryptodome`.

## Usage

The client prepares a request from a dict of parameters and verifies the response. Parameter values are validated on construction (`ValueError` on an unknown parameter or an invalid value, `TypeError` when `amount` is not a `Decimal`); `order` has 12 characters (4 digits followed by 8 alphanumerics), and `amount` is a `Decimal`, serialized to integer minor units on the wire. The allowed values for `currency`, `transaction_type` and `consumer_language` are in `redsys.constants`.

## Using *redirect connection*

### 1. Build a signed request

```python
from decimal import Decimal, ROUND_HALF_UP
from redsys.client import RedirectClient
from redsys.constants import EUR, STANDARD_PAYMENT

client = RedirectClient(secret_key="sq7HjrUOBfKmC576ILgskD5srU870gJ7")

post_parameters = client.prepare_request({
    "merchant_code": "999008881",
    "terminal": "1",
    "transaction_type": STANDARD_PAYMENT,
    "currency": EUR,
    "order": "000000000001",
    # The amount is a Decimal; pre-quantize to two decimals.
    "amount": Decimal("10.56489").quantize(Decimal(".01"), ROUND_HALF_UP),
    "merchant_url": "https://example.com/redsys/response",
    "url_ok": "https://example.com/ok",
    "url_ko": "https://example.com/ko",
    "merchant_name": "Example Commerce",
    "product_description": "Products of Example Commerce",
})  # Ds_SignatureVersion / Ds_MerchantParameters / Ds_Signature
```

The secret key, merchant code `999008881` and terminal `1` are the RedSys public test merchant's. `Ds_MerchantParameters` and `Ds_Signature` are returned as `bytes`; decode them before rendering them in an HTML form.

Bizum: add `"payment_method": "z"` (and optionally `"mobile_number"`) to the parameters.

### 2. Communication step

Auto-submit an HTML form (`method="POST"`) with the three `post_parameters` fields to the RedSys endpoint:

- Test: `https://sis-t.redsys.es:25443/sis/realizarPago`
- Production: `https://sis.redsys.es/sis/realizarPago`

RedSys notifies the result both as a server-to-server POST to `merchant_url` and as a browser redirect to `url_ok` / `url_ko`.

### 3. Verify and read the response

`create_response()` takes the received `Ds_Signature` and `Ds_MerchantParameters` and raises `ValueError` on signature mismatch.

```python
response = client.create_response(signature, merchant_parameters)  # as RedSys posted them back

if response.is_paid:
    ...  # actions after a successful payment
else:
    raise Exception(f"declined with code {response.code}")
```

Response predicates (per the RedSys documentation):

- `response.is_paid`: response code between 0 and 99.
- `response.is_canceled`: response code 400.
- `response.is_refunded`: response code 900.
- `response.is_authorized`: paid, refunded or canceled.

`response.code` is the RedSys code as an `int`, and `response.message` its Spanish description (`None` for a code without one). Decoded fields (`response.order`, `response.amount` as a `Decimal`, ...) read as attributes, `None` when absent; `response.parameters` holds every decoded parameter: listed ones under their attribute name (`amount`), unlisted ones under their original `Ds_*` key.

## Signature version

The 1.x line signs with `HMAC_SHA256_V1` (3DES + HMAC-SHA256), the legacy scheme still accepted by RedSys. `HMAC_SHA512_V1` requires 2.x.

## Support

The 1.x line receives fixes until 2026-12-31.

## Contributing

Contributions that keep the *lightweight* philosophy are welcome.
