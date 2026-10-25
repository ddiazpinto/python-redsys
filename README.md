# Welcome to python-redsys!

[![CI](https://github.com/ddiazpinto/python-redsys/actions/workflows/ci.yml/badge.svg)](https://github.com/ddiazpinto/python-redsys/actions/workflows/ci.yml) [![Coverage](https://codecov.io/gh/ddiazpinto/python-redsys/branch/master/graph/badge.svg)](https://codecov.io/gh/ddiazpinto/python-redsys) [![PyPI](https://img.shields.io/pypi/v/python-redsys.svg)](https://pypi.org/project/python-redsys/) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

A simple, lightweight client to handle payments through the RedSys platform, covering both connection types it defines: *redirect connection* (browser form POST) and *direct connection* (server-to-server REST).

The library builds the signed request and verifies and parses the response. The redirect form is submitted by the cardholder's browser; the direct REST call is made by the integrator's HTTP client or by the optional `http` extra (`httpx`).

For Django, see [django-redsys](https://github.com/ddiazpinto/django-redsys).

## Installation

```bash
pip install python-redsys

# optional: the direct-connection sender (httpx)
pip install "python-redsys[http]"
```

Requires Python 3.10+. Runtime dependencies: `cryptography` and `pydantic` (v2).

## Status

| | |
|---|---|
| Version | 2.0.0; 1.x receives fixes until 2026-12-31 |
| Python | 3.10 to 3.15 |
| RedSys documents followed | Redirection guide 4.2 (2026-02-04), REST guide 4.0.1 (2025-10-17), Bizum guide 2.6 (2026-08-25) |
| Signature versions | `HMAC_SHA512_V2` (default), `HMAC_SHA512_V1`, `HMAC_SHA256_V1` |
| Verified against the RedSys test environment | Redirect connection in a browser, with the 3DS challenge, for all three signature versions (2026-10-25); direct connection end to end (3DS initialization, challenged payment, refund, stored-card token charged as a merchant-initiated payment) on demand by the *Live* workflow |
| Not yet verified live | Frictionless 3DS and the 3DSMethod step |

## Upgrading from 1.x

2.0 has a new API. The [migration guide](docs/migration-1x-to-2x.md) lists every change; 1.x receives fixes until 2026-12-31.

## Usage

The client is the single entry point: an operation method (`payment`, `preauthorization`, `confirmation`, `refund`, `cancellation`) returns a `Request`, with `.to_dict()` for the redirect POST fields and `.send()` for the direct REST call. Fields are validated on construction; `amount` is a `Decimal`. A parameter the library does not model yet is passed by its wire name (`Ds_Merchant_...`), sent as given, with an `UnknownParameterWarning`.

## Using *redirect connection*

### 1. Build a signed request

```python
from decimal import Decimal, ROUND_HALF_UP
from redsys import currencies
from redsys.clients import RedirectClient

client = RedirectClient(
    secret_key="123456789abcdef",
    merchant_code="100000001",
    terminal=1,
    sandbox=False,
)

post_parameters = client.payment(
    order="000000001",
    currency=currencies.EUR,
    # The amount is a Decimal; pre-quantize to two decimals.
    amount=Decimal("10.56489").quantize(Decimal(".01"), ROUND_HALF_UP),
    merchant_url="https://example.com/redsys/response",
    url_ok="https://example.com/ok",
    url_ko="https://example.com/ko",
    merchant_name="Example Commerce",
    product_description="Products of Example Commerce",
).to_dict()  # Ds_SignatureVersion / Ds_MerchantParameters / Ds_Signature
```

Bizum: add `pay_methods="z"` (and optionally `bizum_mobile_number`) to the payment.

### 2. Communication step

Auto-submit an HTML form (`method="POST"`) to `client.endpoint` with the three `post_parameters` fields. RedSys notifies the result both as a server-to-server POST to `merchant_url` and as a browser redirect to `url_ok` / `url_ko`.

### 3. Verify and read the response

`parse_response()` accepts the received parameters (callback form fields or REST JSON body) and raises `ValueError` on signature mismatch.

```python
response = client.parse_response(received)  # received: the Ds_* dict RedSys posted back

if response.is_paid():
    ...  # actions after a successful payment
else:
    raise Exception(f"declined with code {response.response_code}")
```

Response predicates (per the RedSys documentation):

- `response.is_paid()`: response code between 0 and 99.
- `response.is_canceled()`: response code 400.
- `response.is_refunded()`: response code 900.
- `response.is_authorized()`: paid, refunded or canceled.

`response.response_code` is the raw RedSys code; meanings are listed in [`docs/response-codes.md`](docs/response-codes.md). Decoded fields (`response.order`, `response.amount` as a `Decimal`, ...) read off the model; parameters the library does not list are kept under their wire name in `response.model_extra`.

## Using *direct connection* (REST)

The direct connection exchanges the same signed envelope server-to-server as JSON. Build the operation with the same methods: `.send()` performs the call, `.to_dict()` returns the JSON body for your own HTTP client.

With the optional sender (`pip install "python-redsys[http]"`):

```python
from decimal import Decimal
from redsys import currencies
from redsys.clients import DirectClient

client = DirectClient(secret_key="123456789abcdef", merchant_code="100000001",
                      terminal=1, sandbox=True)

response = client.refund(
    order="000000001", amount=Decimal("10.56"), currency=currencies.EUR,
).send()  # signs, POSTs, verifies, parses
response.is_refunded()
```

Asynchronous (`httpx.AsyncClient`), with `send()` awaitable:

```python
from redsys.clients import AsyncDirectClient

client = AsyncDirectClient(secret_key="123456789abcdef", merchant_code="100000001",
                           terminal=1, sandbox=True)
response = await client.payment(
    order="000000001", amount=Decimal("10.56"), currency=currencies.EUR,
    pan="...", expiry_date="2512", cvv2="...",
).send()
```

Transport-agnostic (do your own HTTP):

```python
body = client.refund(order="000000001", amount=Decimal("10.56"),
                     currency=currencies.EUR).to_dict()  # JSON body to POST
# ... POST body to client.endpoint with your HTTP client ...
response = client.parse_response(received_json)  # verifies and parses
```

`parse_response()` raises `redsys.exceptions.ResponseError` when RedSys answers with an error code instead of a signed result.

## inSite (hosted fields)

inSite captures the card in the browser via RedSys's JavaScript and yields an `idoper` token, keeping the PAN off your server. The card-capture JS is the front-end's responsibility; the backend completes the operation as a direct payment carrying the token:

```python
client.payment(order="000000001", amount=Decimal("10.56"), currency=currencies.EUR,
               idoper="<token from the inSite JS>").send()
```

## Tokenization and recurring (COF / MIT)

Store a card on the first payment and charge it later without card data. The first payment requests a token and flags the credential-on-file intent; RedSys returns a token and a COF transaction id that subsequent merchant-initiated charges reuse.

```python
from decimal import Decimal
from redsys import cof, currencies, sca
from redsys.clients import DirectClient

client = DirectClient(secret_key="123456789abcdef", merchant_code="100000001",
                      terminal=1, sandbox=True)

# 1. First payment, request a token (cardholder present)
response = client.payment(
    order="000000001", amount=Decimal("10.56"), currency=currencies.EUR,
    pan="...", expiry_date="YYMM", cvv2="...",
    identifier=cof.REQUEST_TOKEN, cof_ini=cof.INITIAL, cof_type=cof.RECURRING,
).send()
token, cof_txnid = response.identifier, response.cof_txnid

# 2. Later merchant-initiated charge, no card data
client.payment(
    order="000000002", amount=Decimal("10.56"), currency=currencies.EUR,
    identifier=token, cof_ini=cof.SUBSEQUENT, cof_type=cof.RECURRING, cof_txnid=cof_txnid,
    excep_sca=sca.MIT, direct_payment="true",
).send()
```

`redsys.cof` provides the indicator constants (`INITIAL`/`SUBSEQUENT`, `RECURRING`/`INSTALLMENT`/...) and the `REQUEST_TOKEN` sentinel. The token and COF fields are also accepted by `RedirectClient.payment()`, so the first payment can run on the RedSys page. The periodic fields (`sum_total`, `date_frequency`, `charge_expiry_date`) are accepted by `DirectClient.payment()`. `redsys.sca` holds the PSD2 exemption codes for `excep_sca` (`LWV`, `TRA`, `MIT`, `COR`, `ATD`); `sca.QUERY` on `inicia()` asks which exemptions the card allows, returned in `response.excep_sca`.

## Signature versions

`signature_version` on the client constructor selects the scheme; the constants are in `redsys.clients`.

- `HMAC_SHA512_V2` (AES-128 + HMAC-SHA512): the default, as in RedSys's redirection guide and libraries.
- `HMAC_SHA512_V1`: the same algorithm with padded encoding, as in the REST guide.
- `HMAC_SHA256_V1` (3DES): legacy, still accepted by RedSys.

## Reference

- [`docs/response-codes.md`](docs/response-codes.md): response-code meanings.
- [`docs/redirect-connection.md`](docs/redirect-connection.md) / [`docs/direct-connection.md`](docs/direct-connection.md): connection-type protocol reference.

## Contributing

Dev setup, checks and live tests are in [`CONTRIBUTING.md`](CONTRIBUTING.md); contributors are listed in [`CONTRIBUTORS.md`](CONTRIBUTORS.md).
