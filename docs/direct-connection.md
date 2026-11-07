# Direct connection reference

Reference for the RedSys TPV Virtual *direct connection* ("conexión directa"): the merchant's server calls RedSys server to server, with no browser redirect for the request. RedSys offers two flavors:

- REST, JSON over the `/sis/rest/` endpoints, with the same signed three-field envelope as the redirect connection. `DirectClient` and `AsyncDirectClient` implement it.
- SOAP, XML over `/sis/services/SerClsWSEntrada`, the legacy flavor superseded by REST. Not supported.

Without RedSys's hosted pages, the merchant runs the browser steps of 3-D Secure (the 3DSMethod iframe and the challenge form) and, when it handles card data, carries the PCI-DSS scope.

## Endpoints

| Use | Environment | URL |
|-----|-------------|-----|
| Operations | Production | `https://sis.redsys.es/sis/rest/trataPeticionREST` |
| Operations | Test | `https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST` |
| 3DS initialization | Production | `https://sis.redsys.es/sis/rest/iniciaPeticionREST` |
| 3DS initialization | Test | `https://sis-t.redsys.es:25443/sis/rest/iniciaPeticionREST` |

The integration (`environments.INTE`) and development (`environments.DESA`) environments use the same paths; access to them depends on RedSys. The client sends operations to `client.endpoint` and the `inicia_*` methods to `client.inicia_endpoint`.

`endpoint=` on an operation sends that request to another HTTPS URL; it is not signed. `client.url(path)` joins the client's environment host and a path from `redsys.environments`. Bizum Request-to-Pay uses its own paths:

| Constant | Path | Purpose |
|----------|------|---------|
| `RTP_CHECK_PATH` | `/sis/rest/RTP/checkRtpUsuario` | Whether the customer can receive a payment request |
| `RTP_TRATA_PATH` | `/sis/rest/RTP/trataPeticionREST` | Payment (types 0 and 7), refund without original (34) |
| `RTP_BACKUP_PATH` | `/sis/rest/RTP/respaldarUsuarioRTP` | Backup: sends the one-time password |
| `RTP_BACKUP_VALIDATION_PATH` | `/sis/rest/RTP/validarRespaldoUsuarioRTP` | Backup: validates the one-time password |

These calls take `pay_methods=pay_methods.BIZUM` and `bizum_mobile_number`; the backup validation also takes `otp`:

```python
from redsys import environments, generate_order, pay_methods

response = client.payment(
    order=generate_order(), amount=Decimal("10.56"),
    pay_methods=pay_methods.BIZUM, bizum_mobile_number="+34700000000",
    endpoint=client.url(environments.RTP_TRATA_PATH),
).send()
response.rtp_status  # bizum.RTP_OK or bizum.RTP_KO
```

The answer carries `rtp_status`, `rtp_response` (a `BIZnnnnn` code, constants in `redsys.bizum`), `rtp_description` and, when a backup is possible, `rtp_backup_html` or `rtp_backup_template` (Base64).

## Envelope

The request and the response are JSON objects with the three fields of the redirect connection, signed the same way:

```json
{
  "Ds_SignatureVersion": "HMAC_SHA512_V2",
  "Ds_MerchantParameters": "<Base64URL of the Ds_Merchant_* JSON>",
  "Ds_Signature": "<signature over Ds_MerchantParameters>"
}
```

`request.send()` posts `request.to_dict()` to `request.endpoint` with httpx (the `http` extra), verifies the answer and returns a `Response` (`await request.send()` on `AsyncDirectClient`); its keyword arguments go to httpx, with `timeout` at `redsys.clients.DEFAULT_TIMEOUT` (30 seconds) unless given. Without httpx, any HTTP client posts `request.to_dict()` as JSON and passes the JSON answer to `client.parse_response()`.

A failure at the processing level (bad signature, decode error) comes back as `{"errorCode": "SISnnnn"}` instead of a signed result, and raises `ResponseError`.

## 3-D Secure

Card data sent by the merchant goes through EMV 3DS v2 (REST guide 4.0.1, section 6). `redsys.threeds` builds each `Ds_Merchant_EMV3DS` object and `redsys.emv3ds` names its values; the browser steps are the merchant's.

| Step | Request | python-redsys |
|------|---------|---------------|
| 1. Initialization (`iniciaPeticionREST`) | `threeDSInfo` `CardData` | `client.inicia_payment()`, `inicia_preauthorization()` or `inicia_authentication()`; `emv3ds` defaults to `threeds.card_data()` |
| 2. 3DSMethod (optional, browser) | A hidden iframe posts the form field `threeDSMethodData` to `threeDSMethodURL` | `threeds.method_data(three_ds_server_trans_id=..., notification_url=...)`, posted to `response.three_ds_method_url` |
| 3. Authentication (`trataPeticionREST`) | `threeDSInfo` `AuthenticationData`, browser data, `threeDSCompInd` | The operation method with `emv3ds=threeds.authentication_data(..., browser=threeds.browser_info(...), three_ds_comp_ind=emv3ds.METHOD_COMPLETED)` |
| 4. Challenge (browser) | A form posts `creq` to `acsURL`; the ACS posts `cres` back to `notificationURL` | `response.requires_challenge()`, `response.acs_url`, `response.creq` |
| 5. After the challenge (`trataPeticionREST`) | `threeDSInfo` `ChallengeResponse` with `cres` | `client.challenge_response(cres=..., protocol_version=..., transaction_type=...)`; `transaction_type` defaults to `transactions.AUTHORIZATION` |

- The initialization answers `protocolVersion` (`response.protocol_version`; `emv3ds.NO_3DS_V2` when the card has no 3DS v2, see `response.is_no_3ds()`), `threeDSServerTransID` (`response.three_ds_server_trans_id`) and, for some cards, `threeDSMethodURL`.
- `threeDSCompInd` is `emv3ds.METHOD_COMPLETED` when the 3DSMethod finishes within 10 seconds and `emv3ds.METHOD_FAILED` otherwise or when there is no `threeDSMethodURL`.
- The authentication either ends frictionless, with the final `Ds_Response`, or asks for a challenge, with no `Ds_Response`.
- The `protocolVersion` of steps 3 and 5 must not exceed the one of the initialization. EMV3DS sub-field names are case-sensitive.

## Request parameters

Shared with the redirect connection (see its reference): the parameters of every operation, card data (`pan`, `expiry_date`, `cvv2`, `idoper`, `emv3ds`), stored credentials (`identifier`, `cof_ini`, `cof_type`, `cof_txnid`, `group`, `email_titular`, `direct_payment`), `excep_sca`, `merchant_descriptor` and, on payments, `merchant_url`, `pay_methods`, `bizum_mobile_number`, `bizum_mrt_amount_variation`, `tax_reference` and `ota`. Direct only:

| Parameter | Argument | Format | Use |
|-----------|----------|--------|-----|
| `Ds_Merchant_ClientIP` | `client_ip` | AN, 15 | Customer IP address. |
| `Ds_Merchant_Excep_SCA` | `excep_sca` | A, 3 | Besides the exemptions, `sca.QUERY` on the 3DS initialization asks which ones the card allows (`response.excep_sca`). `sca.MIT` goes with `direct_payment=options.DIRECT_PAYMENT`. |
| `Ds_Merchant_DCC` | `dcc` | A or JSON | Dynamic currency conversion: `options.DCC_QUERY` on the 3DS initialization asks for an offer (`response.dcc`); the accepted offer goes in the payment. |
| `Ds_Merchant_Financing` | `financing` | A or JSON | `options.FINANCING_QUERY` on the 3DS initialization asks for financing options; the chosen one goes in the payment. Payments only. |
| `Ds_Merchant_MpiExternal` | `mpi_external` | JSON | Results of an external 3DS server. |
| `Ds_Merchant_TokenData` | `token_data` | JSON | Network token cryptogram data. |
| `Ds_Merchant_SumTotal` | `sum_total` | N | Total of a recurring series, a `Decimal` scaled like `amount`. Payments only. |
| `Ds_Merchant_DateFrecuency` | `date_frequency` | N | Days between recurring charges (RedSys spells it "Frecuency"). |
| `Ds_Merchant_ChargeExpiryDate` | `charge_expiry_date` | `yyyy-MM-dd` | End date of a recurring series. |
| `Ds_Merchant_MatchingData` / `Ds_Acquirer_Identifier` | `matching_data` / `acquirer_identifier` | AN, 21 / N, 6 | PUCE authentication (`transactions.AUTHENTICATION_PUCE`); sent together. |
| `Ds_Merchant_Otp` | `otp` | N | Bizum Request-to-Pay backup: the one-time password. Payments only. |
| `Ds_Merchant_AuthorisationCode` | `authorization_code` | AN, 6 | Refund: authorization code of the original operation. |
| `Ds_Merchant_TransactionDate` | `transaction_date` | `yyyy-mm-dd` | Refund: date of the original operation. |
| `Ds_Merchant_RTS` | `rts` | N, 24 | Refund of a partial confirmation: its `response.rts`. |
| `Ds_Merchant_Customer_Mobile` / `Ds_Merchant_Customer_Mail` | `customer_mobile` / `customer_mail` | AN, 19 / AN, 100 | PayGold: where RedSys sends the link. |
| `Ds_Merchant_Customer_Sms_Text` | `customer_sms_text` | AN, 160 | PayGold SMS; must contain `paygold.SMS_URL`, with the other placeholders of `redsys.paygold` optional. |
| `Ds_Merchant_P2f_ExpiryDate` | `p2f_expiry_date` | AN, 23 | PayGold link expiry: minutes from now, or `yyyy-mm-dd-HH.MM.ss.sss`. |
| `Ds_Merchant_P2f_XmlData` | `p2f_xml_data` | AN, 1000 | PayGold e-mail customization, with the XML tags of `redsys.paygold`. |
| `Ds_Merchant_AltTransType` | `alt_transaction_type` | N | `transactions.REFUND_WITHOUT_ORIGINAL` turns a PayGold link into a refund without original. |
| `DS_XPAYDATA` / `DS_XPAYDECODEDDATA` | `xpay_data` / `xpay_decoded_data` | AN, 10000 / JSON | Google Pay or Apple Pay payload, encrypted, or decrypted by the merchant; one of them, with the two below. Payments and preauthorizations. |
| `DS_XPAYTYPE` | `xpay_type` | AN, 10 | `xpay.GOOGLE` or `xpay.APPLE`. |
| `DS_XPAYORIGEN` | `xpay_origen` | AN, 5 | `xpay.WEB` or `xpay.IN_APP`. |

## Operations

Each method accepts the parameters of its message; any other argument raises `pydantic.ValidationError`, except a wire name (`Ds_Merchant_*`), sent as given with an `UnknownParameterWarning`.

| Types | Methods | Parameters beyond those of every operation |
|-------|---------|--------------------------------------------|
| 0, 7, 8, 15, 34, 51 and types without a method | `payment()`, `authentication()`, `authentication_confirmation()`, `pay_gold()`, `refund_without_original()`, `pay_gold_expiry_change()`, `request(transaction_type, ...)` | All of the above except the refund ones |
| 1, 11 | `preauthorization()`, `request(transactions.REPLACEMENT_PREAUTHORIZATION, ...)` | As payments, without PayGold, Bizum, `merchant_url`, `pay_methods`, `sum_total`, `financing`, `matching_data`, `otp`, `tax_reference` and `ota` |
| 2, 48 | `confirmation()`, `partial_confirmation()` | `merchant_descriptor`, `client_ip` |
| 3 | `refund()` | `merchant_descriptor`, `client_ip`, `authorization_code`, `transaction_date`, `rts` |
| 9, 45, 46, 47 | `void()`, `payment_cancellation()`, `request(transactions.REFUND_CANCELLATION, ...)`, `authentication_confirmation_cancellation()` | `merchant_descriptor`, `client_ip` |

Type constants are in `redsys.transactions`; the full table is in the redirect reference.

### PayGold

`pay_gold()` (`transactions.PAY_GOLD`) creates a payment link that RedSys sends by SMS (`customer_mobile`, `customer_sms_text`) or e-mail (`customer_mail`, `p2f_xml_data`); the link is `response.url_pago_2_fases`. `pay_methods` sets the methods of the link page, several letters together (for example `pay_methods.CARD + pay_methods.BIZUM`). `pay_gold_expiry_change()` (`transactions.PAY_GOLD_EXPIRY_CHANGE`) changes `p2f_expiry_date` of an existing link and needs `amount`.

### Google Pay and Apple Pay

A payment or preauthorization carries the wallet payload in `xpay_data` (encrypted, as the wallet returns it) or `xpay_decoded_data` (decrypted by the merchant), never both, together with `xpay_type` and `xpay_origen`:

```python
from redsys import xpay

client.payment(
    order=generate_order(), amount=Decimal("10.56"),
    xpay_data=wallet_payload, xpay_type=xpay.GOOGLE, xpay_origen=xpay.WEB,
).send()
```

## Response

The answer is verified and parsed like the redirect notification. Besides the fields listed in the redirect reference, `Response` exposes:

| Attribute | Content |
|-----------|---------|
| `identifier`, `cof_txnid` | Card token and network transaction id, when the request asked for a token |
| `emv3ds`, `protocol_version`, `three_ds_server_trans_id`, `three_ds_method_url`, `acs_url`, `creq` | 3-D Secure data; `requires_challenge()` and `is_no_3ds()` read it |
| `excep_sca`, `dcc` | Exemptions the card allows and the currency conversion offer, from the 3DS initialization |
| `rts` | Reference of a partial confirmation, for its refund |
| `url_pago_2_fases` | PayGold link |
| `rtp_status`, `rtp_response`, `rtp_description`, `rtp_backup_html`, `rtp_backup_template` | Bizum Request-to-Pay result |
| `http_status`, `http_headers`, `raw_body` | HTTP details of `send()`; `None` after `parse_response()` |

## Errors

| Situation | Raised |
|-----------|--------|
| RedSys answers `errorCode` instead of a signed result | `ResponseError`; `.error_code` holds the `SISnnnn` code, plus `http_status`, `http_headers` and `raw_body` after `send()` |
| RedSys answers an HTTP error status | `httpx.HTTPStatusError` |
| The signature of the answer does not match | `ValueError` |

`redsys.codes.describe(error.error_code, "en")` gives the meaning of any `SISnnnn` code; [`response-codes.md`](response-codes.md) lists `Ds_Response` and Bizum codes. Common ones in direct integrations:

| Code | Meaning |
|------|---------|
| `SIS0041` / `SIS0042` | Signature calculation error / signature does not match |
| `SIS0429` | Wrong `Ds_SignatureVersion` |
| `SIS0430` | `Ds_MerchantParameters` could not be decoded |
| `SIS0014` | Invalid order format |
| `SIS0051` | Order number already used |
| `SIS0054` / `SIS0056` | Original operation not found / not authorized (refund) |
| `SIS0057` | Refund amount exceeds what is allowed |
| `SIS0573` | Missing `browserAcceptHeader` (3DS) |
| `SIS0585` | EMV 3DS data does not match the initialization |

## Test environment

Same credentials and cards as the redirect reference, against the `sis-t.redsys.es:25443` REST endpoints. `tests/test_live.py` runs this flow end to end, including the challenge on RedSys's simulator ACS.

## Sources

- [Developers portal home](https://pagosonline.redsys.es/desarrolladores-inicio/)
- [Guía de Integración por REST 4.0.1, 2025-10-17, RS.TE.CEL.MAN.0037](https://pagosonline.redsys.es/download/1738/)
- [Área de descargas y documentación](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/area-de-descargas-y-documentacion/)
- [REST integration](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-tipos-de-integracion/desarrolladores-rest/)
- [Parámetros de entrada y salida](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/parametros-de-entrada-y-salida/)
- [Preautorizaciones y confirmaciones](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-operativa/preautorizaciones-y-confirmaciones/)
- [Devolver o anular un pago](https://pagosonline.redsys.es/desarrolladores-inicio/documentacion-operativa/devolver-o-anular-un-pago/)
- [Tarjetas y entornos de prueba](https://pagosonline.redsys.es/desarrolladores-inicio/integrate-con-nosotros/tarjetas-y-entornos-de-prueba/)
- [Bizum guide 2.6](https://pagosonline.redsys.es/download/2053/), [PayGold guide 1.8.2](https://pagosonline.redsys.es/download/2056/), [Google Pay guide 1.9](https://pagosonline.redsys.es/download/2045/), [Apple Pay guide 3.2](https://pagosonline.redsys.es/download/2050/)
