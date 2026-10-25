# Redirect connection reference

Reference for the RedSys TPV Virtual *redirect connection* ("conexión por redirección" / "Realizar Pago"). In this model the merchant builds a signed parameter set, the cardholder's browser auto-POSTs an HTML form to the RedSys endpoint, RedSys runs the payment (including 3-D Secure) on its own pages, and the result comes back two ways: a server-to-server notification POST to `Ds_Merchant_MerchantURL` and a browser redirect to `Ds_Merchant_UrlOK` / `Ds_Merchant_UrlKO`. The library's job is to prepare the request parameters and verify/parse the response; it does not perform any HTTP itself.

This reference follows RedSys's official developer portal (`pagosonline.redsys.es`).

## Endpoints

| Environment | URL |
|-------------|-----|
| Production | `https://sis.redsys.es/sis/realizarPago` |
| Test / sandbox | `https://sis-t.redsys.es:25443/sis/realizarPago` |

## Request

The merchant renders an HTML form that auto-submits (`method="POST"`) to the endpoint with exactly three fields:

| Field | Content |
|-------|---------|
| `Ds_SignatureVersion` | Signature version string. Legacy: `HMAC_SHA256_V1`. Current: `HMAC_SHA512_V1` (REST guide 4.0.1) and `HMAC_SHA512_V2` (redirection guide 4.1 and later; the library default). |
| `Ds_MerchantParameters` | Base64 of a minified JSON object whose keys are the `Ds_Merchant_*` parameters below. `HMAC_SHA256_V1` uses standard Base64; the SHA-512 versions use Base64URL. |
| `Ds_Signature` | Signature over `Ds_MerchantParameters` (see Signature). |

Example decoded `Ds_MerchantParameters` JSON for a minimal authorization (parameter keys are case-insensitive on RedSys's side):

```json
{
  "DS_MERCHANT_ORDER": "00014338z744",
  "DS_MERCHANT_MERCHANTCODE": "999008881",
  "DS_MERCHANT_TERMINAL": "001",
  "DS_MERCHANT_CURRENCY": "978",
  "DS_MERCHANT_TRANSACTIONTYPE": "0",
  "DS_MERCHANT_AMOUNT": "249",
  "DS_MERCHANT_MERCHANTURL": "https://example.com/redsys/notify",
  "DS_MERCHANT_URLOK": "https://example.com/ok",
  "DS_MERCHANT_URLKO": "https://example.com/ko"
}
```

## Request parameters

Minimum required for a standard payment authorization (`transaction_type = 0`):

| Parameter | Type / length | Notes |
|-----------|---------------|-------|
| `Ds_Merchant_MerchantCode` | N, 9 | FUC code assigned by the acquiring bank. |
| `Ds_Merchant_Terminal` | N, 3 | Terminal number (often `001`). |
| `Ds_Merchant_TransactionType` | N, 1+ | Operation code. `0` = standard authorization. See Transaction types. |
| `Ds_Merchant_Amount` | N, up to 12 | Integer in the currency's minor unit (cents). EUR 2.49 -> `249`. |
| `Ds_Merchant_Currency` | N, 4 | ISO-4217 numeric. EUR = `978`. |
| `Ds_Merchant_Order` | AN, up to 12 | First 4 characters numeric; remainder alphanumeric. RedSys recommends 4+ leading digits to avoid collisions. |

Common optional parameters for redirect:

| Parameter | Type / length | Notes |
|-----------|---------------|-------|
| `Ds_Merchant_MerchantURL` | AN, 250 | Server-to-server notification URL. Strongly recommended; without it the only result delivery is the browser redirect. |
| `Ds_Merchant_UrlOK` | AN, 250 | Browser redirect on success. |
| `Ds_Merchant_UrlKO` | AN, 250 | Browser redirect on failure. |
| `Ds_Merchant_MerchantName` | AN, 25 | Shown to the cardholder. |
| `Ds_Merchant_ProductDescription` | AN, 125 | Shown to the cardholder. |
| `Ds_Merchant_Titular` | AN, 60 | Cardholder name. |
| `Ds_Merchant_MerchantData` | AN, 1024 | Opaque merchant data, echoed back in the response. |
| `Ds_Merchant_ConsumerLanguage` | N, 3 | Language code; `0` = undetermined. |
| `Ds_Merchant_Identifier` | N, 40 | Card reference token, or the literal `REQUIRED` to request a new token. |
| `Ds_Merchant_Cof_Ini` / `Ds_Merchant_Cof_Type` / `Ds_Merchant_Cof_TxnId` | AN | Credential-on-file (recurring/tokenized) indicators. |
| `Ds_Merchant_Excep_SCA` | AN, 3 | PSD2 SCA exemption requested: `LWV`, `TRA`, `MIT`, `COR`, `ATD` (REST guide 4.0.1); constants in `redsys.sca`. |
| `Ds_Merchant_DirectPayment` | N | `true` or `moto` to influence authentication. |
| `Ds_Merchant_PayMethods` | A | Payment method offered on the payment page; `z` = Bizum. |
| `Ds_Merchant_Bizum_MobileNumber` | AN, 19 | Customer phone number prefilled on the Bizum page; editable by the customer. |

The full authoritative parameter list (including PayGold, DCC, financing, xPay/Google-Apple Pay, Bizum, and the `Ds_Merchant_EMV3DS` 3-D Secure object) is on the portal's "Parámetros de entrada y salida" page; see Sources.

## Signature

Every message carries a signature over the Base64 `Ds_MerchantParameters` string, keyed by a value derived per operation from the merchant secret and the order number. Three versions exist, selected by `Ds_SignatureVersion`; the library computes and verifies all of them, so only `signature_version` is chosen.

| Version | Cipher / hash | Signature encoding | Specified by |
|---------|---------------|--------------------|--------------|
| `HMAC_SHA256_V1` (legacy) | 3DES + HMAC-SHA256 | standard Base64 | REST guide 4.0.1, Anexo 2 |
| `HMAC_SHA512_V1` | AES-128 + HMAC-SHA512 | Base64URL, keeping the `=` padding | REST guide 4.0.1 (2025-10-17) |
| `HMAC_SHA512_V2` | AES-128 + HMAC-SHA512 | Base64URL without padding | Redirection guide 4.1 and later (2025-09-24), "Firmar una operación", PHP library 2.0.1 |

The two SHA-512 versions share the key derivation and the HMAC and differ only in the `=` padding of the signature (RedSys PHP library 2.0.1, `Signature.php`). `HMAC_SHA512_V2` is the library default; under it `Ds_MerchantParameters` is sent as unpadded Base64URL, which the 3DS initialization endpoint requires (SIS0430 otherwise; verified live 2026-10-25). RedSys's "Firmar una operación" worked example derives the key from the first 16 characters of the secret and order `1234567890` as `RWt3/IPTzYRMXsQtkiGRKg==`.

Response signatures arrive in URL-safe Base64; verification normalizes both sides before a constant-time comparison.

## Response

RedSys returns the result with the same three-field envelope (`Ds_SignatureVersion`, `Ds_MerchantParameters`, `Ds_Signature`), delivered both as a server-to-server POST to `Ds_Merchant_MerchantURL` and via the browser redirect. To process:

1. Base64-decode `Ds_MerchantParameters` and parse the JSON of `Ds_*` fields.
2. Recompute the signature over the received `Ds_MerchantParameters` using `Ds_Order` for the key derivation, normalize URL-safe Base64, and compare to `Ds_Signature`. A mismatch means the response is forged or tampered - reject it.
3. Interpret `Ds_Response`.

## Response parameters

| Parameter | Type / length | Meaning |
|-----------|---------------|---------|
| `Ds_Response` | N, 4 | Result code (see Response codes). |
| `Ds_Amount` | N, 12 | Amount in minor units, echoed. |
| `Ds_Currency` | N, 4 | Currency, echoed. |
| `Ds_Order` | AN, 12 | Order number, echoed. Used to recompute the signature. |
| `Ds_MerchantCode` | N, 9 | Merchant code, echoed. |
| `Ds_Terminal` | N, 3 | Terminal, echoed. |
| `Ds_TransactionType` | AN, 1 | Operation type, echoed. |
| `Ds_AuthorisationCode` | AN, 6 | Issuer authorization code (on success). |
| `Ds_Date` | dd/mm/yyyy | Transaction date. |
| `Ds_Hour` | HH:mm | Transaction time. |
| `Ds_SecurePayment` | N, 1 | 0 unsafe, 1 partial, 2 secure (3DS). |
| `Ds_MerchantData` | AN, 1024 | Echoed merchant data. |
| `Ds_Card_Country` | N, 3 | Issuing country. |
| `Ds_Card_Type` | AN, 1 | `C` credit, `D` debit, `V` voucher, `X` mixed. |
| `Ds_Card_Brand` | N | 1 VISA, 2 Mastercard, 6 Diners, 7 Privada, 8 Amex, 9 JCB. |
| `Ds_Card_Number` | AN | Masked card number (REST responses name it `Ds_CardNumber`; both read as `Response.card_number`). |
| `Ds_ErrorCode` | AN, 7 | `SISxxxx` error code when applicable. |
| `Ds_EMV3DS` | JSON | 3-D Secure authentication response data. |
| `Ds_ProcessedPayMethod` | N, 3 | Payment method the operation was processed with (`68` = Bizum). |
| `Ds_Amount_Euro` | N, 12 | Amount in euros; only for operations in a currency other than the euro. |

## Response codes

`Ds_Response` is a 4-digit code. Authorization outcomes are decided by range:

| Code / range | Meaning |
|--------------|---------|
| `0000`-`0099` | Authorized (payment / preauthorization). |
| `0900` | Authorized refund or confirmation. |
| `0400` | Authorized cancellation. |
| `0100` | Partial authorization (verify against RedSys's docs before relying on it). |
| `>= 0101` (other) | Declined or error; specific code identifies the reason (expired card, CVV, fraud, etc.). |
| `SIS0xxx` / `9xxx` in `Ds_ErrorCode` | Input/processing errors (bad signature, missing field, decode failure). |

The library returns the raw `Ds_Response` code (`Response.response_code`) and does not translate it; English meanings are documented in `docs/response-codes.md`. Helper predicates: `is_paid()` = `0 <= code <= 99`; `is_refunded()` = `code == 900`; `is_canceled()` = `code == 400`; `is_authorized()` = any of those.

## Transaction types

| Code | Operation |
|------|-----------|
| 0 | Authorization (standard payment) |
| 1 | Preauthorization |
| 2 | Preauthorization confirmation (capture) |
| 3 | Refund |
| 7 | Card validation (authentication only) |
| 8 | Authentication confirmation |
| 9 | Preauthorization cancellation |
| 11 | Preauthorization extension |
| 15 | PayGold request (payment link) |
| 17 | PUCE authentication |
| 34 | Refund without original |
| 37 | Gambling prize |
| 44 | Delete token reference |
| 45 | Payment cancellation (48h) |
| 46 | Refund cancellation (48h) |
| 47 | Confirmation cancellation (48h) |
| 48 | Partial preauthorization confirmation |

## Test environment

| Field | Value |
|-------|-------|
| Endpoint | `https://sis-t.redsys.es:25443/sis/realizarPago` |
| Merchant code (FUC) | `999008881` |
| Terminal | `001` |
| Secret key | `sq7HjrUOBfKmC576ILgskD5srU870gJ7` |
| Test card (VISA, EMV3DS 2.2) | `4548810000000003`, exp `12/49`, CVV `123` |
| Test card (Mastercard, EMV3DS 2.1) | `5576441563045037`, exp `12/49`, CVV `123` |

CVV `999` forces a denial; amounts ending in `.96`/`.72`/`.73`/`.74` EUR trigger specific declines.

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
