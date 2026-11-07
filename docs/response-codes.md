# RedSys response codes

`redsys.codes.describe(code, language="es")` returns the meaning of a `Ds_Response` code, an `SISnnnn` error code or a Bizum `BIZnnnnn` code, in Spanish (`"es"`, `languages.SPANISH`), Catalan (`"ca"`, `languages.CATALAN`; Valencian, `"va"` or `languages.VALENCIAN`, reads the same text), Galician (`"gl"`, `languages.GALICIAN`), Basque (`"eu"`, `languages.EUSKERA`) or English (`"en"`, `languages.ENGLISH`); an unknown code or language gives `""`. `response.describe(language)` gives the meaning of a parsed response's `Ds_Response`, or of its `Ds_ErrorCode` when there is none. The texts are written from RedSys's public tables.

```python
from redsys import languages, responses
from redsys.codes import describe

describe(responses.SCA_REQUIRED, languages.ENGLISH)  # 'Soft decline: SCA authentication required'
describe("0195", "en")                              # the same, from the wire value
describe("SIS0051")                                 # Spanish by default
```

## Outcome by range

| Code / range | Outcome | Predicate |
|--------------|---------|-----------|
| `0000`-`0099` | Authorized payment or preauthorization | `is_paid()` |
| `0900` | Authorized refund or confirmation | `is_refunded()` |
| `0400` | Authorized cancellation | `is_canceled()` |
| other | Declined, pending or error | none |

`is_authorized()` is true for any of paid, refunded or canceled. Constants: `responses.AUTHORIZED` to `responses.AUTHORIZED_LAST`, `responses.REFUND_OR_CONFIRMATION_AUTHORIZED` and `responses.CANCELLATION_AUTHORIZED`.

## Ds_Response codes

Constants in `redsys.api.responses` (also `from redsys import responses`).

| Code | Constant | Meaning |
|------|----------|---------|
| `0000`-`0099` | `AUTHORIZED` | Approved payment or pre-authorization |
| `0101` | `CARD_EXPIRED` | Card expired; do not retry |
| `0102` | `CARD_INVALID` | Card invalid; do not retry |
| `0104` | `OPERATION_NOT_ALLOWED_FOR_CARD` | Operation not allowed for this card; ask issuer |
| `0106` | `PIN_ATTEMPTS_EXCEEDED` | Too many PIN attempts |
| `0107` | `CONTACT_ISSUER` | Cardholder should contact the issuer |
| `0110` | `AMOUNT_NOT_ALLOWED` | Amount not allowed for this operation; ask issuer |
| `0112` | `PIN_REQUIRED` | PIN is required |
| `0114` | `CARD_NOT_VALID_FOR_OPERATION` | Card cannot be used for this operation; ask issuer |
| `0115` | `CARD_INVALID_115` | Card invalid; do not retry |
| `0116` | `INSUFFICIENT_FUNDS` | Insufficient funds |
| `0117` | `WRONG_PIN` | Wrong PIN |
| `0118` | `CARD_NOT_REGISTERED` | Card not registered; do not retry |
| `0121` | `TRANSACTION_LIMIT_EXCEEDED` | Transaction limit exceeded; ask issuer |
| `0123` | `CARDHOLDER_AUTHENTICATION_FAILED_ASK_ISSUER` | Cardholder authentication failed; ask issuer |
| `0125` | `CARD_NOT_ACTIVE` | Card not active for use; do not retry |
| `0126` | `AUTHENTICATION_FORMAT_ERROR` | Authentication format error; ask issuer |
| `0129` | `WRONG_SECURITY_CODE` | Wrong security code (CVV2/CVC2) |
| `0130` | `CURRENCY_NOT_SUPPORTED` | Currency not supported by the issuer |
| `0162` | `UNAUTHENTICATED_LIMIT_EXCEEDED` | Limit of unauthenticated transactions exceeded |
| `0163` | `CARD_INACTIVE` | Card inactive |
| `0171` | `CARD_INACTIVE_171` | Card inactive |
| `0172` | `DECLINED_DO_NOT_RETRY` | Declined; brand says never retry |
| `0173` | `DECLINED_UPDATE_CARD_DATA` | Declined; retry only with updated card data |
| `0174` | `DECLINED_RETRY_AFTER_72_HOURS` | Declined; wait 72 hours before retrying |
| `0180` | `CARD_NOT_ACCEPTED` | Card not accepted by this service |
| `0181` | `CARD_DEBIT_RESTRICTED` | Card has debit restrictions |
| `0182` | `CARD_CREDIT_RESTRICTED` | Card has credit restrictions |
| `0184` | `CARDHOLDER_AUTHENTICATION_FAILED` | Cardholder authentication failed |
| `0187` | `AUTHENTICATION_FORMAT_ERROR_187` | Authentication format error; ask issuer |
| `0190` | `DECLINED_BY_ISSUER` | Issuer declined without a stated reason |
| `0191` | `WRONG_EXPIRY_DATE` | Wrong expiry date |
| `0193` | `AMOUNT_EXCEEDED` | Amount exceeded |
| `0195` | `SCA_REQUIRED` | Soft decline: SCA authentication required |
| `0201` | `CARD_INVALID_201` | Card invalid; do not retry |
| `0202` | `CARD_BLOCKED_RETAIN` | Card under temporary block or fraud suspicion; retain |
| `0204` | `OPERATION_NOT_ALLOWED_FOR_CARD_OR_TERMINAL` | Operation not allowed for this card or terminal |
| `0206` | `PIN_ATTEMPTS_EXCEEDED_DO_NOT_RETRY` | Too many PIN attempts; do not retry |
| `0290` | `DECLINED` | Declined without a stated reason |
| `0300` | `UPDATE_OR_QUERY_COMPLETED` | Update or query completed |
| `0400` | `CANCELLATION_AUTHORIZED` | Cancellation (void) approved |
| `0481` | `CANCELLATION_AUTHORIZED_LATE` | Cancellation approved despite excessive delay |
| `0881` | `SIGN_OFF_WITHOUT_SESSION` | Sign-off message without an open session |
| `0900` | `REFUND_OR_CONFIRMATION_AUTHORIZED` | Refund or confirmation approved (also PUCE authentication) |
| `0904` | `MERCHANT_NOT_REGISTERED` | Merchant not registered in FUC |
| `0909` | `SYSTEM_ERROR` | System error |
| `0912` | `ISSUER_UNAVAILABLE` | Issuer unavailable |
| `0913` | `DUPLICATE_ORDER` | Duplicate order |
| `0940` | `ALREADY_CANCELED` | Transaction already canceled |
| `0941` | `ORIGINAL_AUTHORIZATION_DECLINED` | Original authorization was declined |
| `0944` | `INVALID_SESSION` | Wrong session |
| `0945` | `DUPLICATE_SYSTEM_REFERENCE` | Duplicate system transaction reference |
| `0950` | `REFUND_NOT_ALLOWED` | Refund not allowed |
| `0965` | `RULES_BREACH` | Breach of existing rules |
| `8210` | `SENT_FOR_EMV3DS_2_1_AUTHENTICATION` | Sent to issuer for EMV3DS 2.1 authentication |
| `8220` | `SENT_FOR_EMV3DS_2_2_AUTHENTICATION` | Sent to issuer for EMV3DS 2.2 authentication |
| `9064` | `WRONG_CARD_NUMBER_LENGTH` | Card number has the wrong length |
| `9078` | `TRANSACTION_TYPE_NOT_ALLOWED_FOR_CARD` | Transaction type not allowed for this card |
| `9093` | `CARD_DOES_NOT_EXIST` | Card does not exist |
| `9094` | `REJECTED_BY_INTERNATIONAL_SERVERS` | Rejected by international servers |
| `9104` | `CARDHOLDER_WITHOUT_SECURE_KEY` | Secure-only merchant, cardholder without secure purchase key |
| `9218` | `SECURE_OPERATIONS_NOT_ALLOWED` | Merchant forbids secure operations on this entry |
| `9253` | `CARD_CHECK_DIGIT_FAILED` | Card number fails the check digit |
| `9256` | `MERCHANT_CANNOT_PREAUTHORIZE` | Merchant cannot make pre-authorizations |
| `9257` | `CARD_CANNOT_PREAUTHORIZE` | Card does not allow pre-authorizations |
| `9261` | `ENTRY_RESTRICTION_STOP` | Stopped by SIS entry restriction controls |
| `9915` | `CANCELED_BY_USER` | Payment canceled by the user |
| `9997` | `CARD_OPERATION_IN_PROGRESS` | Another transaction with the same card in progress |
| `9998` | `WAITING_FOR_CARD_DATA` | Waiting for card data entry |
| `9999` | `SENT_FOR_AUTHENTICATION` | Sent to issuer for authentication |

## SIS error codes

`SISnnnn` codes arrive in `errorCode` (REST, raised as `ResponseError`) or `Ds_ErrorCode` (redirect). Each has a numeric twin `9nnn` that may arrive in `Ds_Response`; a `9nnn` code without its own row above has the meaning of `SIS0nnn`. `describe()` covers every code of RedSys's public table.

## Bizum codes

Returned in `Ds_RtpResponse` (`response.rtp_response`) by the Bizum Request-to-Pay services; constants in `redsys.bizum`.

| Code | Meaning |
|------|---------|
| `BIZ00000` | Request processed successfully |
| `BIZ00001` | A required input parameter is missing |
| `BIZ00002` | An input parameter has an invalid format |
| `BIZ00003` | The requested item was not found |
| `BIZ00005` | Internal system failure |
| `BIZ00006` | Security check failed (3DES / MAC X9.19) |
| `BIZ00007` | Operation not allowed |
| `BIZ00008` | Payee not found |
| `BIZ00009` | Payer not found (customer has no Bizum) |
| `BIZ00202` | Feature not implemented yet (seen when the customer lacks RTP) |
| `BIZ00213` | Authentication of the incoming request failed (security sequence) |
| `BIZ00224` | Issuer answered KO to the RTP authentication |
| `BIZ00225` | RTP authentication did not complete successfully |
| `BIZ00233` | Authentication failed but the operation can be backed up (respaldo) |
