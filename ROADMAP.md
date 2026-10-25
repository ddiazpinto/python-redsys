# Roadmap

Forward-looking only. Completed work lives in `CHANGELOG.md`.

## Pending

- [ ] Decide on SOAP direct connection: ship a `soap` extra or keep it out of scope.
- [ ] Confirm transaction types 8, 11 and 44-48 against the reference and add them to `redsys.conf.transactions` if wanted.
- [ ] Decide whether 2.x supports the 1.x transaction types with no 2.0 equivalent: recurring 5 and 6, and the deferred pre-authorization family O, P, Q, R and S (`transaction_type` is an integer in the models).

## Before production

- [ ] Exercise the redirect connection against the test environment (needs a browser hop).
- [ ] Exercise the EMV3DS frictionless path and the 3DSMethod step against the test environment (the default test card always challenges).

## Ideas

- [ ] Model the dynamic currency conversion objects: `Ds_Merchant_DCC` on the request and the `Ds_DCC` object of the 3DS initialization response (portal, Operativa DCC).
- [ ] `Ds_MerchantPartialPayment` response field: seen only in a community fork; confirm with RedSys before modeling.

## Design notes
