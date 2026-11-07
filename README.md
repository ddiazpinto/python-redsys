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
| Version | 2.1.0; 1.x receives fixes until 2026-12-31 |
| Python | 3.10 to 3.15 |
| RedSys documents followed | Redirection guide 4.2 (2026-02-04), REST guide 4.0.1 (2025-10-17), Bizum guide 2.6 (2026-08-25), inSite guide 4.1 (2026-01-05), PayGold guide 1.8.2 (2026-04-20), Google Pay guide 1.9 (2025-05-21), Apple Pay guide 3.2 (2023-03-28), "Parámetros de entrada y salida" page |
| Signature versions | `HMAC_SHA512_V2` (default), `HMAC_SHA512_V1`, `HMAC_SHA256_V1` |
| Verified against the RedSys test environment | Redirect connection in a browser, with the 3DS challenge, for all three signature versions (2026-10-25); direct connection end to end (3DS initialization, frictionless payment with and without the 3DSMethod step, challenged payment, refund, preauthorization void, payment cancellation, stored-card token charged as a merchant-initiated payment) on demand by the *Live* workflow |

## Upgrading from 1.x

2.0 has a new API. The [migration guide](docs/migration-1x-to-2x.md) lists every change; 1.x receives fixes until 2026-12-31.

## Usage

The client is the single entry point: an operation method (`payment`, `preauthorization`, `confirmation`, `refund`, `void`, ...) returns a `Request`, with `.to_dict()` for the redirect POST fields and `.send()` for the direct REST call. Fields are validated on construction; `amount` is a `Decimal`. A parameter the library does not model yet is passed by its wire name (`Ds_Merchant_...`), sent as given, with an `UnknownParameterWarning`. Documented values have named constants in modules of `redsys` (`transactions`, `currencies`, `languages`, `options`, `cards`, `emv3ds`, `processed_pay_methods`, `secure_payment`, ...).

## Environments and API key

`environment` selects `DESA`, `INTE`, `TEST` or `PROD` (constants in `redsys.environments`). `sandbox=True` equals `TEST` and `sandbox=False` equals `PROD`; a contradictory pair raises `ValidationError`.

`from_api_key()` builds any client from a RedSys API key, which carries the environment, merchant code, terminal and secret key:

```python
client = RedirectClient.from_api_key(api_key, signature_version="HMAC_SHA512_V2")
```

An invalid key raises `redsys.exceptions.ValidationError`. `repr(client)` shows no secret.

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

request = client.payment(
    order="000000001",
    currency=currencies.EUR,
    # The amount is a Decimal; pre-quantize to two decimals.
    amount=Decimal("10.56489").quantize(Decimal(".01"), ROUND_HALF_UP),
    merchant_url="https://example.com/redsys/response",
    url_ok="https://example.com/ok",
    url_ko="https://example.com/ko",
    merchant_name="Example Commerce",
    product_description="Products of Example Commerce",
)
post_parameters = request.to_dict()  # Ds_SignatureVersion / Ds_MerchantParameters / Ds_Signature
```

`currency` defaults to `currencies.EUR`; `currency=` on the client constructor sets another default, and a value in the call wins.

The redirect connection takes `payment()`, `preauthorization()`, `authentication()` and `refund_without_original()`; any other transaction type raises `ValidationError`.

`redsys.generate_order()` returns a random order number: 4 digits, then letters and digits, 12 characters unless `length` (4 to 12) says otherwise.

Bizum: add `pay_methods=pay_methods.BIZUM` (`"z"`, and optionally `bizum_mobile_number`) to the payment. `redsys.pay_methods` holds the other payment-method values. `bizum_id_oper` (from `response.bizum_id_oper`) asks RedSys to run the Bizum backup, and `bizum_mrt_amount_variation` sets the ceiling of later merchant-initiated amounts.

### 2. Communication step

Auto-submit an HTML form (`method="POST"`) to `request.endpoint` with the three `post_parameters` fields. RedSys notifies the result both as a server-to-server POST to `merchant_url` and as a browser redirect to `url_ok` / `url_ko`.

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

`response.response_code` is the raw RedSys code, with names in `redsys.responses`; `response.describe()` gives its meaning in Spanish, `response.describe("en")` in English, and `redsys.codes.describe(code)` does the same for any `Ds_Response`, `SISnnnn` or Bizum `BIZnnnnn` code ([`docs/response-codes.md`](docs/response-codes.md)). Decoded fields (`response.order`, `response.amount` as a `Decimal`, ...) read off the model; parameters the library does not list are kept under their wire name in `response.model_extra`.

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

`endpoint=` on any operation sends that request to another HTTPS URL, for example Bizum Request-to-Pay:

```python
from redsys import environments

client.payment(order="000000001", amount=Decimal("1.00"), pay_methods="z",
               bizum_mobile_number="+34700000000",
               endpoint=client.url(environments.RTP_TRATA_PATH)).send()
```

Request-to-Pay answers carry `response.rtp_status` (`bizum.RTP_OK` or `bizum.RTP_KO`) and `response.rtp_response`, a `BIZnnnnn` code named in `redsys.bizum`; `otp=` goes to `environments.RTP_BACKUP_VALIDATION_PATH`.

After `send()`, `http_status`, `http_headers` and `raw_body` on the `Response` and on `ResponseError` hold the HTTP exchange; after `parse_response()` they are `None`.

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

## PayGold (payment by link)

`pay_gold()` registers a payment link and RedSys sends it by SMS or e-mail; `response.url_pago_2_fases` holds the link. `customer_sms_text` must contain `paygold.SMS_URL`; `p2f_expiry_date` takes minutes or `yyyy-mm-dd-HH.MM.ss.sss`, and `pay_gold_expiry_change()` changes it later.

```python
from redsys import paygold

response = client.pay_gold(
    order="000000001", amount=Decimal("10.56"), customer_mobile="600000000",
    customer_sms_text=f"{paygold.SMS_AMOUNT} {paygold.SMS_CURRENCY}: {paygold.SMS_URL}",
    p2f_expiry_date=60,
).send()
link = response.url_pago_2_fases
```

## Google Pay and Apple Pay

A direct payment or preauthorization carries the wallet payload in `xpay_data` (encrypted) or `xpay_decoded_data` (decrypted by the merchant), with `xpay_type` (`xpay.GOOGLE`, `xpay.APPLE`) and `xpay_origen` (`xpay.WEB`, `xpay.IN_APP`); they go on the wire as `DS_XPAY*`.

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

- `HMAC_SHA512_V2` (AES-128 + HMAC-SHA512): the default, as in RedSys's redirection guide.
- `HMAC_SHA512_V1`: the same algorithm with padded encoding, as in the REST guide.
- `HMAC_SHA256_V1` (3DES): legacy, still accepted by RedSys.

## Reference

- [`docs/response-codes.md`](docs/response-codes.md): response, SIS and Bizum code meanings.
- [`docs/redirect-connection.md`](docs/redirect-connection.md) / [`docs/direct-connection.md`](docs/direct-connection.md): connection-type protocol reference.
- [`docs/official-libraries.md`](docs/official-libraries.md): equivalences for PHP and Java integrators.

## Contributing

Dev setup, checks and live tests are in [`CONTRIBUTING.md`](CONTRIBUTING.md); contributors are listed in [`CONTRIBUTORS.md`](CONTRIBUTORS.md).
