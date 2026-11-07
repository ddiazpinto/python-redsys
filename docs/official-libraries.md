# Equivalences for PHP and Java integrators

Reference for projects moving to python-redsys from RedSys's PHP or Java integration libraries. Operation names and types come from RedSys's public "Parámetros de entrada y salida" table.

## Operations

| RedSys name | Type | Connection | python-redsys |
|-------------|------|------------|---------------|
| Autorización | 0 | redirect, REST | `payment()` |
| Preautorización | 1 | redirect, REST | `preauthorization()` |
| Confirmación de preautorización | 2 | REST | `confirmation()` |
| Devolución | 3 | REST | `refund()` |
| Validación de tarjeta (autenticación) | 7 | redirect, REST | `authentication()` |
| Confirmación de autenticación | 8 | REST | `authentication_confirmation()` |
| Anulación de preautorización | 9 | REST | `void()` |
| Paygold, solicitud de pago | 15 | REST | `pay_gold()` |
| Devolución sin original | 34 | redirect, REST | `refund_without_original()` |
| Anulación de pago | 45 | REST | `payment_cancellation()` |
| Anulación de devolución | 46 | REST | `request(transactions.REFUND_CANCELLATION, ...)` |
| Anulación de confirmación de autenticación | 47 | REST | `authentication_confirmation_cancellation()` |
| Confirmación parcial de preautorización | 48 | REST | `partial_confirmation()` |
| Paygold, cambio de caducidad del enlace | 51 | REST | `pay_gold_expiry_change()` |

Any other type goes through `client.request(transaction_type, ...)`. An operation method rejects a `transaction_type` different from its own. The redirect client accepts types 0, 1, 7 and 34 only; any other raises `ValidationError`.

PayGold: `pay_gold()` sends type 15, the value of the parameters table; the PayGold guide writes the type as `F`. The test environment accepts 15 and answers `Ds_TransactionType` `"F"`. Type 51 comes from the PayGold guide and needs `amount`.

`cancellation()` sends type 9. It is deprecated in favor of `void()` and is removed in 3.0.

## 3-D Secure

| Step | python-redsys |
|------|---------------|
| Initialization | `inicia_payment()`, `inicia_preauthorization()`, `inicia_authentication()`; `emv3ds` defaults to `threeds.card_data()` |
| 3DSMethod | `threeds.method_data(three_ds_server_trans_id=..., notification_url=...)`, the `threeDSMethodData` form field the browser posts to `response.three_ds_method_url` |
| Authentication data | The operation method with `emv3ds=threeds.authentication_data(...)` |
| After the challenge | `challenge_response(cres=..., protocol_version=..., transaction_type=...)`; `transaction_type` defaults to `transactions.AUTHORIZATION` |

## Configuration

| Concept | python-redsys |
|---------|---------------|
| API key | `Client.from_api_key(api_key)` on every client |
| Environment | `environment=` (`DESA`, `INTE`, `TEST`, `PROD`), or `sandbox=` for `TEST` and `PROD` |
| Signature version | `signature_version=`; `HMAC_SHA512_V2` by default |
| Default currency | Euro; `currency=` on the client sets another one |
| Endpoint of one request | `endpoint=` on the operation, an HTTPS URL; `client.url(path)` with the paths in `redsys.environments` (Bizum Request-to-Pay) |

## Payment methods and parameters

| Concept | python-redsys |
|---------|---------------|
| Payment method on the redirect page | `pay_methods=` with `redsys.pay_methods` (`BIZUM`, `CARD`, `BANK_TRANSFER`, `PAYPAL`, `XPAY`, `GOOGLE_PAY`) |
| Bizum Request-to-Pay | `pay_methods=pay_methods.BIZUM`, `bizum_mobile_number` and `endpoint=client.url(environments.RTP_TRATA_PATH)` on the operation; `rtp_status`, `rtp_response` and `rtp_description` on the `Response`; codes in `redsys.bizum` |
| PayGold link | `pay_gold()` with `customer_mail`, `customer_mobile`, `customer_sms_text` (holding `paygold.SMS_URL`), `p2f_expiry_date`; the link is `response.url_pago_2_fases` |
| Google Pay and Apple Pay | `xpay_data` or `xpay_decoded_data`, with `xpay_type` (`xpay.GOOGLE`, `xpay.APPLE`) and `xpay_origen` (`xpay.WEB`, `xpay.IN_APP`) |
| Order number | `redsys.generate_order(length=12)`: 4 digits, then letters and digits |
| Code descriptions | `redsys.codes.describe(code, language)` for `Ds_Response`, `SISnnnn` and `BIZnnnnn` codes, in Spanish, Catalan (also Valencian), Galician, Basque or English; `response.describe()` |
| Option values | Constants in `redsys` (`transactions`, `currencies`, `languages`, `pay_methods`, `cof`, `sca`, `options`, `emv3ds`, `xpay`, `paygold`, `bizum`, `environments`, `cards`, `processed_pay_methods`, `secure_payment`, `responses`) |
| Parameter without a field | Passed by its wire name (`Ds_Merchant_...`), sent as given with an `UnknownParameterWarning` |

## Library behavior

| Topic | python-redsys |
|-------|---------------|
| Amounts | `Decimal` in major units (`Decimal("10.56")`); the wire value in minor units is computed from the currency |
| Clients | Instances that hold the credentials; every operation is a method of the client |
| Invalid API key | Raises `redsys.exceptions.ValidationError` |
| Redirect connection | No I/O and no HTML: `request.to_dict()` gives the three form fields and `request.endpoint` the form `action` |
| 3-D Secure forms | Built by the integrator from `response.acs_url` and `response.creq` |
| HTTP details | `http_status`, `http_headers` and `raw_body` on `Response` and `ResponseError` after `send()` |
