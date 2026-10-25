# RedSys response codes (Ds_Response)

The library returns the raw code as `response.response_code` (and the raw string as `response.response`). This table gives the meaning of the common codes so you can build your own user-facing, localized messages from the code - which is the recommended approach (the code is the stable contract; the wording is yours).

## Outcome by range

| Code / range | Outcome | Predicate |
|--------------|---------|-----------|
| `0000`-`0099` | Authorized (payment / pre-authorization) | `is_paid()` |
| `0900` | Authorized refund or confirmation | `is_refunded()` |
| `0400` | Authorized cancellation | `is_canceled()` |
| `0101`+ (other) | Declined or error (see below) | none |
| `SISxxxx` / `9xxx` | Input or processing error (bad signature, missing field, decode failure) | none |

`is_authorized()` is true for any of paid / refunded / canceled.

## Common codes

| Code | Meaning |
|------|---------|
| 0000 | Transaction authorized for payments and pre-authorizations |
| 0900 | Transaction authorized for refunds and confirmations |
| 0400 | Transaction authorized for cancellations |
| 0101 | Expired card |
| 0102 | Card under temporary exception or suspected fraud |
| 0106 | PIN attempts exceeded |
| 0125 | Card not active |
| 0129 | Incorrect security code (CVV2/CVC2) |
| 0180 | Card not accepted / out of service |
| 0184 | Cardholder authentication error |
| 0190 | Issuer declined without specifying a reason |
| 0172 | Declined, do not retry |
| 0173 | Declined, do not retry without updating the card data |
| 0174 | Declined, do not retry before 72 hours |
| 0191 | Incorrect expiry date |
| 0195 | Requires SCA authentication; retry through the EMV3DS flow (the test environment describes it as "EMISOR EXIGE AUTENTICACIÓN") |
| 0202 | Card under temporary exception or suspected fraud, with card retention |
| 0904 | Merchant not registered in FUC |
| 0909 | System error |
| 0912 | Issuer unavailable |
| 0913 | Duplicate order |
| 0944 | Invalid session |
| 0950 | Refund operation not allowed |
| 9912 | Issuer unavailable |
| 9064 | Incorrect number of card digits |
| 9078 | Operation type not allowed for this card |
| 9093 | Card does not exist |
| 9094 | Rejected by international servers |
| 9104 | Merchant requires secure authentication but the cardholder has no secure-payment key |
| 9218 | Merchant does not allow secure operations through this entry |
| 9253 | Card fails the check digit |
| 9256 | Merchant cannot perform pre-authorizations |
| 9568 | Initialization request (iniciaPeticionREST) rejected: wrong transaction type (SIS0568) |
| 9257 | This card does not allow pre-authorizations |
| 9261 | Operation stopped: exceeded the SIS entry restriction control |
| 9913 | Error in the confirmation the merchant sends to the Virtual POS |
| 9914 | Merchant "KO" (negative) confirmation |
| 9915 | Payment cancelled at the user's request |
| 9928 | Deferred authorization cancellation performed by SIS (batch process) |
| 9929 | Deferred authorization cancellation performed by the merchant |
| 9997 | Another transaction with the same card is being processed in SIS |
| 9998 | Operation in process of requesting card data |
| 9999 | Operation redirected to the issuer for authentication |

The authoritative and complete list (including all `SISxxxx` input/processing errors) is RedSys's "TPV-Virtual GuiaErroresSIS" spreadsheet, available from the developer portal's downloads area.
