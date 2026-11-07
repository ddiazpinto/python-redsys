# Equivalences for PHP and Java integrators

Reference for projects moving to python-redsys from RedSys's PHP or Java integration libraries. Operation names and types come from RedSys's public "Parámetros de entrada y salida" table.

## Operations

| RedSys name | Type | Connection | python-redsys |
|-------------|------|------------|---------------|
| Autorización | 0 | redirect, REST | `payment()` |
| Preautorización | 1 | redirect, REST | `preauthorization()` |
| Confirmación de preautorización | 2 | REST | `confirmation()` |
| Devolución | 3 | REST | `refund()` |
| Validación de tarjeta (autenticación) | 7 | redirect, REST | `authentication()` (REST); `request(transactions.AUTHENTICATION, ...)` (redirect) |
| Confirmación de autenticación | 8 | REST | `authentication_confirmation()` |
| Anulación de preautorización | 9 | REST | `void()` |
| Paygold, solicitud de pago | 15 | REST | `pay_gold()` |
| Anulación de pago | 45 | REST | `payment_cancellation()` |
| Anulación de devolución | 46 | REST | `request(transactions.REFUND_CANCELLATION, ...)` |
| Anulación de confirmación de autenticación | 47 | REST | `authentication_confirmation_cancellation()` |
| Confirmación parcial de preautorización | 48 | REST | `partial_confirmation()` |

Any other type goes through `client.request(transaction_type, ...)`. An operation method rejects a `transaction_type` different from its own.

`cancellation()` sends type 9. It is deprecated in favor of `void()` and is removed in 3.0.

## 3-D Secure

| Step | python-redsys |
|------|---------------|
| Initialization | `inicia_payment()`, `inicia_preauthorization()`, `inicia_authentication()`; `emv3ds` defaults to `threeds.card_data()` |
| Authentication data | The operation method with `emv3ds=threeds.authentication_data(...)` |
| After the challenge | `challenge_response(cres=..., protocol_version=..., transaction_type=...)`; `transaction_type` defaults to 0 |

## Configuration

| Concept | python-redsys |
|---------|---------------|
| API key | `Client.from_api_key(api_key)` on every client |
| Environment | `environment=` (`DESA`, `INTE`, `TEST`, `PROD`), or `sandbox=` for `TEST` and `PROD` |
| Signature version | `signature_version=`; `HMAC_SHA512_V2` by default |
| Default currency | Euro; `currency=` on the client sets another one |

## Library behavior

| Topic | python-redsys |
|-------|---------------|
| Amounts | `Decimal` in major units (`Decimal("10.56")`); the wire value in minor units is computed from the currency |
| Clients | Instances that hold the credentials; every operation is a method of the client |
| Invalid API key | Raises `redsys.exceptions.ValidationError` |
| Redirect connection | No I/O and no HTML: `request.to_dict()` gives the three form fields and `request.endpoint` the form `action` |
| 3-D Secure forms | Built by the integrator from `response.acs_url` and `response.creq` |
| HTTP details | `http_status`, `http_headers` and `raw_body` on `Response` and `ResponseError` after `send()` |
