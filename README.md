# python-redsys

[![CI](https://github.com/ddiazpinto/python-redsys/actions/workflows/ci.yml/badge.svg)](https://github.com/ddiazpinto/python-redsys/actions/workflows/ci.yml) [![Coverage](https://codecov.io/gh/ddiazpinto/python-redsys/branch/master/graph/badge.svg)](https://codecov.io/gh/ddiazpinto/python-redsys) [![PyPI](https://img.shields.io/pypi/v/python-redsys.svg)](https://pypi.org/project/python-redsys/) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

A lightweight client for the RedSys TPV Virtual: it builds signed requests and verifies and parses responses, for the *redirect connection* (browser form) and the *direct connection* (server-to-server REST). For Django, see [django-redsys](https://github.com/ddiazpinto/django-redsys).

## Installation

```bash
pip install python-redsys
pip install "python-redsys[http]"  # optional: sends direct-connection requests with httpx
```

Python 3.10 or later. Runtime dependencies: `cryptography` and `pydantic` 2.

## Redirect connection

```python
from decimal import Decimal
from redsys import generate_order
from redsys.clients import RedirectClient

client = RedirectClient(secret_key="...", merchant_code="999008881", terminal=1, sandbox=True)

# 1. Build the signed request.
request = client.payment(
    order=generate_order(),
    amount=Decimal("10.56"),  # euros unless currency= says otherwise
    merchant_url="https://example.com/redsys/notification",
    url_ok="https://example.com/ok",
    url_ko="https://example.com/ko",
)

# 2. The browser POSTs request.to_dict() (three fields) to request.endpoint.

# 3. Verify and read the notification RedSys posts to merchant_url.
response = client.parse_response(received_fields)
if response.is_paid():
    ...
else:
    print(response.response_code, response.describe("en"))
```

The redirect connection takes `payment()`, `preauthorization()`, `authentication()` and `refund_without_original()`.

## Direct connection

```python
from redsys.clients import DirectClient

client = DirectClient(secret_key="...", merchant_code="999008881", terminal=1, sandbox=True)

response = client.refund(order="000000001", amount=Decimal("10.56")).send()  # signs, posts, verifies
response.is_refunded()
```

- `AsyncDirectClient` has the same methods; `await request.send()`.
- Without the `http` extra, POST `request.to_dict()` to `request.endpoint` with any HTTP client and pass the JSON answer to `client.parse_response()`.
- Operations: `payment`, `preauthorization`, `confirmation`, `partial_confirmation`, `refund`, `refund_without_original`, `void`, `payment_cancellation`, `authentication`, `authentication_confirmation`, `pay_gold`, and `request(transaction_type, ...)` for any other type in `redsys.transactions`.

## 3-D Secure

Card data sent by the merchant goes through EMV3DS. The library builds each call; the browser steps (3DSMethod iframe, challenge form) are the integrator's.

```python
from redsys import emv3ds, threeds

card = dict(pan="4548810000000003", expiry_date="4912", cvv2="123")
operation = dict(order=generate_order(), amount=Decimal("10.56"))

config = client.inicia_payment(**operation, **card).send()
# Optional 3DSMethod: the browser posts threeds.method_data(...) to config.three_ds_method_url.

authentication = threeds.authentication_data(
    three_ds_server_trans_id=config.three_ds_server_trans_id,
    notification_url="https://example.com/redsys/3ds",
    protocol_version=config.protocol_version,
    browser=threeds.browser_info(...),  # collected by the merchant page
    three_ds_comp_ind=emv3ds.METHOD_COMPLETED,
)
response = client.payment(emv3ds=authentication, **operation, **card).send()

if response.requires_challenge():
    # The browser posts response.creq to response.acs_url; the ACS posts cres back to notification_url.
    response = client.challenge_response(
        cres=cres, protocol_version=response.protocol_version, **operation, **card
    ).send()
```

## Stored cards and merchant-initiated payments

```python
from redsys import cof, options, sca

first = client.payment(..., identifier=cof.REQUEST_TOKEN, cof_ini=cof.INITIAL, cof_type=cof.RECURRING)
# After 3-D Secure: first.identifier is the token, first.cof_txnid the network transaction id.

client.payment(
    order=generate_order(), amount=Decimal("10.56"),
    identifier=token, cof_txnid=cof_txnid, cof_ini=cof.SUBSEQUENT, cof_type=cof.RECURRING,
    excep_sca=sca.MIT, direct_payment=options.DIRECT_PAYMENT,
).send()
```

## Payment methods

- **Bizum, redirect:** `pay_methods=pay_methods.BIZUM` on `payment()`.
- **Bizum Request-to-Pay, direct:** the same, plus `bizum_mobile_number` and `endpoint=client.url(environments.RTP_TRATA_PATH)`; read `response.rtp_status` and `response.rtp_response` (`redsys.bizum`).
- **PayGold link:** `pay_gold(customer_mobile=..., customer_sms_text=f"{paygold.SMS_AMOUNT} {paygold.SMS_URL}")`; the link is `response.url_pago_2_fases`.
- **Google Pay and Apple Pay:** `xpay_data` (or `xpay_decoded_data`) with `xpay_type=xpay.GOOGLE` and `xpay_origen=xpay.WEB`.
- **inSite:** `idoper=` with the token from RedSys's JavaScript, on a direct `payment()`.

## Configuration

| Option | Use |
|---|---|
| `environment=` | `environments.TEST`, `PROD`, `INTE` or `DESA`; `sandbox=True` is `TEST` |
| `Client.from_api_key(api_key)` | Reads the environment, merchant code, terminal and secret key from a RedSys API key |
| `currency=` | Default currency of the client (`currencies.EUR` unless set); a call can override it |
| `signature_version=` | `HMAC_SHA512_V2` (default), `HMAC_SHA512_V1` or legacy `HMAC_SHA256_V1`, from `redsys.clients` |
| `module=` | `Ds_Merchant_Module` of every request: `python-redsys/<version>` by default, another text, or `None` to leave it out |
| `endpoint=` on an operation | Sends that request to another HTTPS URL; `client.url(path)` builds one |

Every documented value has a named constant in `redsys` (`transactions`, `currencies`, `languages`, `pay_methods`, `cof`, `sca`, `options`, `emv3ds`, `cards`, `responses`, ...). Use them instead of literals.

## Errors

Fields are validated when the operation method is called, before anything is signed or sent. Any invalid parameter raises a `ValueError` subclass:

| Problem | Raised |
|---|---|
| A field with the wrong type or format, a missing required field, a misspelled or 1.x field name, an unknown currency or transaction type | `pydantic.ValidationError`; `.errors()` lists each field |
| A transaction type that contradicts the operation or the redirect connection, a non-HTTPS `endpoint`, an invalid API key or environment | `redsys.exceptions.ValidationError` |
| A signature that does not match in `parse_response()` | `ValueError` |
| RedSys answers with an error code instead of a signed result | `redsys.exceptions.ResponseError`; `.error_code` holds the `SISnnnn` code |
| An HTTP error status from RedSys in `send()` | `httpx.HTTPStatusError` |

A parameter the library does not model yet can be passed by its wire name (`Ds_Merchant_...`): it is sent as given, with an `UnknownParameterWarning`.

## Response codes

`response.response_code` is the integer `Ds_Response`; `response.is_paid()` (0 to 99), `is_refunded()` (900), `is_canceled()` (400) and `is_authorized()` (any of them) cover the common outcomes. `response.describe(language)` and `redsys.codes.describe(code, language)` give the meaning of any `Ds_Response`, `SISnnnn` or Bizum `BIZnnnnn` code. Table: [`docs/response-codes.md`](docs/response-codes.md).

## Status

| | |
|---|---|
| Version | 2.1.0; 1.x receives fixes until 2026-12-31 ([migration guide](docs/migration-1x-to-2x.md)) |
| Python | 3.10 to 3.15 |
| RedSys documents followed | Redirection guide 4.2, REST guide 4.0.1, Bizum guide 2.6, inSite guide 4.1, PayGold guide 1.8.2, Google Pay guide 1.9, Apple Pay guide 3.2, "Parámetros de entrada y salida" page |
| Verified against the RedSys test environment | Redirect in a browser with the 3DS challenge; direct end to end (frictionless and challenged 3DS, 3DSMethod, refund, void, payment cancellation, stored-card merchant-initiated charge), in all three signature versions |

## Reference

- [`docs/redirect-connection.md`](docs/redirect-connection.md) and [`docs/direct-connection.md`](docs/direct-connection.md): protocol reference for each connection.
- [`docs/response-codes.md`](docs/response-codes.md): response, SIS and Bizum codes.
- [`docs/official-libraries.md`](docs/official-libraries.md): equivalences for integrators of RedSys's PHP and Java libraries.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): development setup, checks and live tests.
