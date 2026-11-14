# Redirect connection reference

Reference for the RedSys TPV Virtual *redirect connection* ("conexión por redirección", "Realizar Pago"). The cardholder's browser posts a signed form to RedSys; RedSys runs the payment, 3-D Secure included, on its own pages and returns the result twice: a server-to-server notification to `Ds_Merchant_MerchantURL` and a browser redirect to `Ds_Merchant_UrlOK` or `Ds_Merchant_UrlKO`. `RedirectClient` builds the form fields and verifies and parses the result; it performs no HTTP.

## Endpoints

| Environment | Constant | URL |
|-------------|----------|-----|
| Production | `environments.PROD` | `https://sis.redsys.es/sis/realizarPago` |
| Test | `environments.TEST` | `https://sis-t.redsys.es:25443/sis/realizarPago` |
| Integration | `environments.INTE` | `https://sis-i.redsys.es:25443/sis/realizarPago` |
| Development | `environments.DESA` | `https://sis-d.redsys.es/sis/realizarPago` |

`request.endpoint` is the URL of the client's environment (`environment=`, or `sandbox=True` for `TEST`); `endpoint=` on an operation replaces it for that request. Access to the integration and development environments depends on RedSys.

## Request

The form posts three fields, `request.to_dict()`, to `request.endpoint`:

| Field | Content |
|-------|---------|
| `Ds_SignatureVersion` | `HMAC_SHA512_V2` (default), `HMAC_SHA512_V1` or legacy `HMAC_SHA256_V1`; see Signature. |
| `Ds_MerchantParameters` | JSON object of the `Ds_Merchant_*` parameters, in unpadded Base64URL under `HMAC_SHA512_V2` and in standard Base64 under the other versions. |
| `Ds_Signature` | Signature over `Ds_MerchantParameters`. |

Decoded `Ds_MerchantParameters` of `client.payment(order="00014338z744", amount=Decimal("2.49"), merchant_url=..., url_ok=..., url_ko=...)` (RedSys reads the keys case-insensitively):

```json
{
  "Ds_Merchant_Amount": 249,
  "Ds_Merchant_Currency": 978,
  "Ds_Merchant_MerchantCode": "999008881",
  "Ds_Merchant_MerchantURL": "https://example.com/redsys/notification",
  "Ds_Merchant_Order": "00014338z744",
  "Ds_Merchant_Terminal": 1,
  "Ds_Merchant_TransactionType": 0,
  "Ds_Merchant_UrlKO": "https://example.com/ko",
  "Ds_Merchant_UrlOK": "https://example.com/ok"
}
```

## Request parameters

Each parameter is an argument of the operation method (column Argument); the wire name is accepted too.

Every operation:

| Parameter | Argument | Format | Notes |
|-----------|----------|--------|-------|
| `Ds_Merchant_MerchantCode` | `merchant_code` | N, 9 | FUC code assigned by the acquiring bank; usually set on the client. |
| `Ds_Merchant_Terminal` | `terminal` | N, 3 | Terminal number, 1 to 999; usually set on the client. |
| `Ds_Merchant_TransactionType` | set by the method | N | See Transaction types. |
| `Ds_Merchant_Amount` | `amount` | N, 12 | `Decimal` in major units, sent in the currency's minor units: `Decimal("2.49")` in euros is `249`. |
| `Ds_Merchant_Currency` | `currency` | N, 4 | ISO 4217 numeric code from `redsys.currencies`; `currencies.EUR` unless the client or the call sets another. |
| `Ds_Merchant_Order` | `order` | AN, 4 to 12 | 4 digits, then up to 8 letters or digits; unique per merchant. `redsys.generate_order()` draws one. |

Optional:

| Parameter | Argument | Format | Notes |
|-----------|----------|--------|-------|
| `Ds_Merchant_MerchantURL` | `merchant_url` | AN, 250 | Server-to-server notification URL. Without it the browser redirect is the only result delivery. |
| `Ds_Merchant_UrlOK` / `Ds_Merchant_UrlKO` | `url_ok` / `url_ko` | AN, 250 | Browser redirect on success / failure. |
| `Ds_Merchant_MerchantName` | `merchant_name` | AN, 25 | Shown to the cardholder. |
| `Ds_Merchant_ProductDescription` | `product_description` | AN, 125 | Shown to the cardholder. |
| `Ds_Merchant_Titular` | `titular` | AN, 60 | Cardholder name. |
| `Ds_Merchant_MerchantData` | `merchant_data` | AN, 1024 | Merchant data, echoed in the response. |
| `Ds_Merchant_ConsumerLanguage` | `consumer_language` | N, 3 | Payment page language from `redsys.languages`; `languages.DEFAULT` (0) is undetermined. |
| `Ds_Merchant_PayMethods` | `pay_methods` | A | Method offered on the payment page, from `redsys.pay_methods`: `BIZUM`, `CARD`, `BANK_TRANSFER`, `PAYPAL`, `XPAY` (Google Pay and Apple Pay buttons) or `GOOGLE_PAY`. |
| `Ds_Merchant_Bizum_MobileNumber` | `bizum_mobile_number` | AN, 19 | Customer phone number prefilled on the Bizum page; the customer can change it. |
| `Ds_Merchant_Bizum_MrtAmountVariation` | `bizum_mrt_amount_variation` | N | Bizum: ceiling for later merchant-initiated amounts, in minor units, on the operation that creates the stored credential. Types 0, 7 and 34. |
| `Ds_Merchant_Bizum_IdOper` | `bizum_id_oper` | AN | Bizum: `response.bizum_id_oper` of an operation, to ask RedSys for its backup. Types 0, 7 and 34. |
| `Ds_Merchant_Identifier` | `identifier` | AN, 40 | Stored-card token, or `cof.REQUEST_TOKEN` to ask for a new one. |
| `Ds_Merchant_Cof_Ini` / `Ds_Merchant_Cof_Type` / `Ds_Merchant_Cof_Txnid` | `cof_ini` / `cof_type` / `cof_txnid` | A, 1 / A, 1 / AN, 15 | Credential-on-file indicators, values in `redsys.cof`. |
| `Ds_Merchant_Group` | `group` | N, 9 | Group that shares card tokens; with `identifier`. |
| `Ds_Merchant_DirectPayment` | `direct_payment` | A | `options.DIRECT_PAYMENT` skips authentication; `options.MOTO` marks a mail or telephone order. |
| `Ds_Merchant_Excep_SCA` | `excep_sca` | A, 3 | PSD2 SCA exemption requested, from `redsys.sca`: `LWV`, `TRA`, `MIT`, `COR`, `ATD`. |
| `Ds_Merchant_MerchantDescriptor` | `merchant_descriptor` | AN, 25 | Soft descriptor; needs bank activation. |
| `Ds_Merchant_Email_Titular` | `email_titular` | AN, 100 | Cardholder e-mail; RedSys sends a purchase summary. |
| `Ds_Merchant_ShippingAddressPyP` | `shipping_address_pyp` | A, 1 | `options.SHIPPING_ADDRESS` returns the PayPal shipping address, `options.NO_SHIPPING_ADDRESS` does not. |
| `Ds_Merchant_PersoCode` | `perso_code` | N, 1 | Payment page personalization. |
| `Ds_Merchant_Tax_Reference` | `tax_reference` | AN, 100 | Tax payment barcode; needs bank activation. Types 0, 7 and 34. |
| `Ds_Merchant_OTA` | `ota` | A, 1 | `options.OTA_INITIAL` on the initial authentication (type 7) of an online travel agency. Types 0, 7 and 34. |
| `Ds_Merchant_Pan` / `Ds_Merchant_ExpiryDate` / `Ds_Merchant_Cvv2` | `pan` / `expiry_date` / `cvv2` | N | Card data sent by the merchant (PCI-DSS scope); expiry as `YYMM`. |
| `Ds_Merchant_Idoper` | `idoper` | AN, 40 | inSite operation token. |
| `Ds_Merchant_EMV3DS` | `emv3ds` | JSON | Cardholder and address data for the issuer; RedSys collects the browser data itself. |

A parameter without an argument goes by its wire name, sent as given with an `UnknownParameterWarning`. The full parameter list is on the portal's "Parámetros de entrada y salida" page; see Sources.

## Signature

Every message carries a signature over the `Ds_MerchantParameters` string, keyed by a value derived per operation from the merchant secret and the order number. `signature_version=` on the client selects the version; responses are verified in the version they name.

| Version | Cipher / hash | Signature encoding | Specified by |
|---------|---------------|--------------------|--------------|
| `HMAC_SHA256_V1` (legacy) | 3DES + HMAC-SHA256 | standard Base64 | REST guide 4.0.1, Anexo 2 |
| `HMAC_SHA512_V1` | AES-128 + HMAC-SHA512 | Base64URL, keeping the `=` padding | REST guide 4.0.1 (2025-10-17) |
| `HMAC_SHA512_V2` | AES-128 + HMAC-SHA512 | Base64URL without padding | Redirection guide 4.1 and later (2025-09-24), "Firmar una operación" |

The two SHA-512 versions share the key derivation and the HMAC and differ only in the `=` padding of the signature, as signed responses of the test environment show. The 3DS initialization endpoint requires unpadded Base64URL `Ds_MerchantParameters` under `HMAC_SHA512_V2` and answers SIS0430 otherwise. RedSys's "Firmar una operación" worked example derives the key from the first 16 characters of the secret and order `1234567890` as `RWt3/IPTzYRMXsQtkiGRKg==`.

Response signatures arrive in URL-safe Base64; verification normalizes both sides before a constant-time comparison.

## Response

RedSys returns the result in the same three-field envelope, both as a server-to-server POST to `Ds_Merchant_MerchantURL` and through the browser redirect. `client.parse_response(fields)` decodes `Ds_MerchantParameters`, recomputes the signature with the key derived from `Ds_Order`, compares it with `Ds_Signature` and only then validates the fields into a `Response`. A mismatch raises `ValueError`: the fields did not come from RedSys or were altered. A payload that is not a well-formed result raises `redsys.exceptions.ValidationError`, also a `ValueError`: not a mapping, neither `Ds_MerchantParameters` nor an error code, no `Ds_Signature` or one over 128 characters, an unsupported `Ds_SignatureVersion`, a `Ds_MerchantParameters` over 128 KiB or that is not a Base64-encoded JSON object nested at most 32 levels (all checked before the signature), or a signed field the model rejects. An error code without `Ds_MerchantParameters` raises `ResponseError`; it carries no signature, so it does not prove that RedSys sent it.

## Response parameters

| Parameter | Attribute | Format | Meaning |
|-----------|-----------|--------|---------|
| `Ds_Response` | `response`, `response_code` | N, 4 | Result code, as text and as an integer; see Response codes. |
| `Ds_Amount` | `amount` | N, 12 | Amount, a `Decimal` in major units of `Ds_Currency`. |
| `Ds_Currency` | `currency` | N, 4 | Currency. |
| `Ds_Order` | `order` | AN, 12 | Order number; derives the signature key. |
| `Ds_MerchantCode` | `merchant_code` | N, 9 | Merchant code. |
| `Ds_Terminal` | `terminal` | N, 3 | Terminal. |
| `Ds_TransactionType` | `transaction_type` | AN, 1 | Transaction type, as text. |
| `Ds_AuthorisationCode` | `authorization_code` | AN, 6 | Issuer authorization code, on success. |
| `Ds_Date` / `Ds_Hour` | `date` / `hour` | dd/mm/yyyy / HH:mm | Transaction date and time. |
| `Ds_SecurePayment` | `secure_payment` | N, 1 | Authentication level, from `redsys.secure_payment`: `NOT_SECURE`, `ATTEMPT`, `SECURE`. |
| `Ds_MerchantData` | `merchant_data` | AN, 1024 | Merchant data of the request. |
| `Ds_Card_Country` | `card_country` | N, 3 | Issuing country. |
| `Ds_Card_Type` | `card_type` | AN, 1 | From `redsys.cards`: `CREDIT`, `DEBIT`, `VOUCHER`, `MIXED`. |
| `Ds_Card_Brand` | `card_brand` | N | From `redsys.cards`: `VISA`, `MASTERCARD`, `DINERS`, `PRIVATE_LABEL`, `AMEX`, `JCB`, `UPI`. |
| `Ds_Card_Number` | `card_number` | AN | Masked card number; REST responses name it `Ds_CardNumber`. |
| `Ds_ErrorCode` | `error_code` | AN, 7 | `SISnnnn` error code, when there is one. |
| `Ds_EMV3DS` | `emv3ds` | JSON | 3-D Secure authentication data. |
| `Ds_ProcessedPayMethod` | `processed_pay_method` | N, 3 | Method the operation was processed with, from `redsys.processed_pay_methods` (`BIZUM` is `68`). |
| `Ds_Amount_Euro` | `amount_euro` | N, 12 | Amount in euros, for operations in another currency; the raw wire value. |
| `Ds_Merchant_Identifier` / `Ds_Merchant_Cof_Txnid` | `identifier` / `cof_txnid` | AN, 40 / AN, 15 | Card token and network transaction id, when the request asked for a token. |
| `Ds_Bizum_IdOper` | `bizum_id_oper` | AN | Bizum operation id. |

`redsys.models.Response` names further fields; a parameter it does not name stays in `response.model_extra` under its wire name.

## Response codes

`Ds_Response` outcomes, the predicates `is_paid()`, `is_refunded()`, `is_canceled()` and `is_authorized()`, and the meaning of every code (`response.describe(language)`) are in [`response-codes.md`](response-codes.md). Processing errors arrive as `SISnnnn` codes in `Ds_ErrorCode`.

## Transaction types

Constants in `redsys.transactions`.

| Code | Constant | Operation |
|------|----------|-----------|
| 0 | `AUTHORIZATION` | Authorization (standard payment) |
| 1 | `PREAUTHORIZATION` | Preauthorization |
| 2 | `CONFIRMATION` | Preauthorization confirmation (capture) |
| 3 | `REFUND` | Refund |
| 7 | `AUTHENTICATION` | Card validation (authentication only) |
| 8 | `AUTHENTICATION_CONFIRMATION` | Authentication confirmation |
| 9 | `VOID` | Preauthorization void |
| 11 | `REPLACEMENT_PREAUTHORIZATION` | Replacement preauthorization (extends a preauthorization) |
| 15 | `PAY_GOLD` | PayGold request (payment link) |
| 17 | `AUTHENTICATION_PUCE` | PUCE authentication |
| 34 | `REFUND_WITHOUT_ORIGINAL` | Refund without original |
| 37 | `BETTING_PRICE` | Betting prize |
| 38 | `PAY_GOLD_AUTHORIZATION` | PayGold authorization (sent by RedSys) |
| 44 | `DELETE_REFERENCE` | Delete a card token |
| 45 | `PAYMENT_CANCELLATION` | Payment cancellation |
| 46 | `REFUND_CANCELLATION` | Refund cancellation, within 48 hours |
| 47 | `AUTHENTICATION_CONFIRMATION_CANCELLATION` | Authentication confirmation cancellation |
| 48 | `PARTIAL_CONFIRMATION` | Partial preauthorization confirmation |
| 51 | `PAY_GOLD_EXPIRY_CHANGE` | PayGold link expiry change |

The redirect connection accepts `transactions.REDIRECT_TRANSACTION_TYPES` (0, 1, 7 and 34), through `payment()`, `preauthorization()`, `authentication()` and `refund_without_original()`; the rest go through the direct connection.

## Test environment

| Field | Value |
|-------|-------|
| Endpoint | `https://sis-t.redsys.es:25443/sis/realizarPago` |
| Merchant code (FUC) | `999008881` |
| Terminal | `001` (`terminal=1`) |
| Secret key | `sq7HjrUOBfKmC576ILgskD5srU870gJ7` |
| Test card (Visa, EMV3DS 2.2) | `4548810000000003`, expiry `12/49`, CVV `123` |
| Test card (Mastercard, EMV3DS 2.1) | `5576441563045037`, expiry `12/49`, CVV `123` |

CVV `999` forces a denial; amounts ending in `.96`, `.72`, `.73` or `.74` EUR trigger specific declines.

## Sources

- [Developers portal home](https://pagosonline.redsys.es/desarrolladores-inicio/)
- [Guía de Integración por Redirección 4.2, 2026-02-04, RS.TE.CEL.MAN.0039](https://pagosonline.redsys.es/download/1735/)
- [Área de descargas y documentación](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/area-de-descargas-y-documentacion/)
- [Redirección integration](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-tipos-de-integracion/desarrolladores-redireccion/)
- [Realizar un pago (autorización)](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-operativa/autorizacion/)
- [Firmar una operación (signature)](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-operativa/firmar-una-operacion/)
- [Parámetros de entrada y salida](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/parametros-de-entrada-y-salida/)
- [Bizum](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-otros-metodos-de-pago/desarrolladores-bizum-1/)
- [Tarjetas y entornos de prueba](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/tarjetas-y-entornos-de-prueba/)
