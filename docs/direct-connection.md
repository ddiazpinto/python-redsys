# Direct connection reference

Reference for the RedSys TPV Virtual *direct connection* ("conexión directa"), where the merchant's server talks to RedSys server-to-server with no browser redirect for the request leg. RedSys offers two technical flavors:

- REST / JSON over the `/sis/rest/` endpoints. Same signed three-field envelope as the redirect method, exchanged as JSON. This is the modern path and the one this library targets first.
- SOAP / XML over `/sis/services/SerClsWSEntrada`, the legacy flavor superseded by REST. Not supported.

Because direct connection skips RedSys's hosted pages, the merchant is responsible for 3-D Secure orchestration (the REST flavor provides a two-step `iniciaPeticionREST` / `trataPeticionREST` flow for EMV 3DS v2) and, for raw card data, for PCI-DSS scope.

## Endpoints

| Flavor | Environment | URL |
|--------|-------------|-----|
| REST | Production | `https://sis.redsys.es/sis/rest/trataPeticionREST` |
| REST | Test | `https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST` |
| REST (3DS init) | Production | `https://sis.redsys.es/sis/rest/iniciaPeticionREST` |
| REST (3DS init) | Test | `https://sis-t.redsys.es:25443/sis/rest/iniciaPeticionREST` |

## REST (JSON) flavor

The envelope is identical to the redirect method - three fields, same signature - but posted as JSON server-to-server and answered with JSON:

```json
{
  "Ds_SignatureVersion": "HMAC_SHA512_V2",
  "Ds_MerchantParameters": "<Base64URL of the Ds_Merchant_* JSON>",
  "Ds_Signature": "<signature over Ds_MerchantParameters>"
}
```

The response is the same shape; Base64-decode `Ds_MerchantParameters`, verify `Ds_Signature`, and read `Ds_Response`. Processing-level failures (bad signature, decode error) are returned as `SISxxxx` codes in an error field rather than a `Ds_Response`.

### 3-D Secure v2 flow (per the official REST manual v4.0.1, section 6)

Card-data SCA is a multi-step flow. The merchant owns the browser hops (the 3DSMethod iframe and the challenge); the library prepares and parses each REST call.

1. inicia (`iniciaPeticionREST`) with `Ds_Merchant_EMV3DS = {"threeDSInfo": "CardData"}`. Response `Ds_EMV3DS`: `protocolVersion` (`NO_3DS_V2` / `1.0.2` / `2.1.0` / `2.2.0`), `threeDSServerTransID`, `threeDSInfo: "CardConfiguration"`, optional `threeDSMethodURL`.
2. (optional) 3DSMethod - a hidden-iframe browser exchange with the issuer that yields `threeDSCompInd` (`Y`/`N`).
3. authorize (`trataPeticionREST`) with `Ds_Merchant_EMV3DS = {"threeDSInfo": "AuthenticationData", "protocolVersion", browser* fields, "threeDSServerTransID", "notificationURL", "threeDSCompInd"}`. Response is either frictionless (final `Ds_Response` 0000-0099) or a challenge: `Ds_EMV3DS = {"threeDSInfo": "ChallengeRequest", "acsURL", "creq"}`; a challenge response carries no `Ds_Response`.
4. (challenge) the merchant POSTs an HTML form to `acsURL` with field `creq`; after authentication the ACS POSTs `cres` back to `notificationURL`.
5. finalize (`trataPeticionREST`) with `Ds_Merchant_EMV3DS = {"threeDSInfo": "ChallengeResponse", "protocolVersion", "cres"}`. Response is the final result.

The `protocolVersion` in the authorize call must not exceed the one returned by inicia, and EMV3DS sub-field names are case-sensitive.

In the library, `redsys.threeds` builds the EMV3DS objects and `DirectClient.inicia()` / `.send()` drive the init and authorize/finalize calls; the parsed `Response` exposes the 3DS fields and predicates (`requires_challenge()`, `acs_url`, `creq`, `is_no_3ds()`).

## Request parameters

Direct connection uses the same `Ds_Merchant_*` set as redirect (see the redirect reference), plus card-data and operation-specific fields:

| Parameter | Type / length | Used for |
|-----------|---------------|----------|
| `Ds_Merchant_Pan` | N, 19 | Card number (raw-card direct payment; PCI scope). |
| `Ds_Merchant_ExpiryDate` | N, 4 | Expiry `YYMM`. |
| `Ds_Merchant_Cvv2` | N, 3-4 | Card security code. |
| `Ds_Merchant_Identifier` | N, 40 | Stored-card token (alternative to raw card data). |
| `Ds_Merchant_AuthorisationCode` | AN, 6 | Required for some refunds/confirmations. |
| `Ds_Merchant_TransactionDate` | AN, 10 | Operation date for deferred/recurring ops. |
| `Ds_Merchant_SumTotal` | N | Total for recurring series (field length not documented). |
| `Ds_Merchant_DateFrecuency` | N | Days between recurring charges (note RedSys's spelling "Frecuency"). |
| `Ds_Merchant_ChargeExpiryDate` | date | End date for a recurring series. |
| `Ds_Merchant_DirectPayment` | N | `true`/`moto` to influence authentication. |
| `Ds_Merchant_Excep_SCA` | AN, 3 | PSD2 SCA exemption requested: `LWV`, `TRA`, `MIT`, `COR`, `ATD`; `Y` on iniciaPeticionREST asks which exemptions the card allows (answer in `Ds_Excep_SCA`). MIT also sends `Ds_Merchant_DirectPayment` = `true`. |

## Signature

Identical to the redirect connection; see the redirect reference.

## Response

REST responses use the three-field envelope; decode and verify exactly as in the redirect flow. Operation-specific response fields appear alongside the standard ones (for example `Ds_Merchant_Identifier` when a token was created, `Ds_EMV3DS` for the authentication result, DCC and financing objects when those features are active).

## Response codes

Same `Ds_Response` semantics as redirect: `0000`-`0099` authorized, `0900` refund/confirmation authorized, `0400` cancellation authorized, others declined/error. Direct-connection input and processing failures surface as `SISxxxx` codes, for example:

| Code | Meaning |
|------|---------|
| `SIS0041` / `SIS0042` | Signature calculation error. |
| `SIS0429` | Invalid signature version. |
| `SIS0430` | `Ds_MerchantParameters` decode error. |
| `SIS0014` | Invalid order format. |
| `SIS0051` | Duplicate order number. |
| `SIS0054` / `SIS0056` | Original operation not found / not authorized (refund). |
| `SIS0057` | Refund exceeds original amount. |
| `SIS0573` | Missing `browserAcceptHeader` (REST/SOAP 3DS). |
| `SIS0585` | EMV 3DS data mismatch with `iniciaPeticion`. |

## Transaction types

Same code table as the redirect reference (0 authorization, 1 preauthorization, 2 confirmation, 3 refund, 9 cancellation, plus recurring, PUCE, PayGold, token-management, and 48h-cancellation codes).

## Test environment

Same credentials and cards as the redirect reference, against the `sis-t.redsys.es:25443` REST endpoints. `tests/test_live.py` exercises this flow end to end, including the challenge on RedSys's simulator ACS.

## Sources

- [Developers portal home](https://pagosonline.redsys.es/desarrolladores-inicio/)
- [Guía de Integración por REST 4.0.1, 2025-10-17, RS.TE.CEL.MAN.0037](https://pagosonline.redsys.es/download/1738/)
- [Librería de integración en PHP 2.0.1](https://pagosonline.redsys.es/download/3214/)
- [Área de descargas y documentación](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/area-de-descargas-y-documentacion/)
- [REST integration](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-tipos-de-integracion/desarrolladores-rest/)
- [Parámetros de entrada y salida](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/parametros-de-entrada-y-salida/)
- [Preautorizaciones y confirmaciones](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-operativa/preautorizaciones-y-confirmaciones/)
- [Devolver o anular un pago](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-operativa/devolver-o-anular-un-pago/)
- [Tarjetas y entornos de prueba](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/tarjetas-y-entornos-de-prueba/)
