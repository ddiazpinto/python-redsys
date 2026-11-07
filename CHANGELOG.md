# Changelog

All notable changes to this project. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Named environments: `environment=` on every client (`DESA`, `INTE`, `TEST`, `PROD`, in `redsys.environments`) resolves the redirect and REST endpoints. `sandbox` keeps working; a contradictory pair raises `ValidationError`.
- `from_api_key()` on every client builds it from a RedSys API key.
- `Request.endpoint`: the URL each request goes to.
- `repr()` of a client shows its account and environment, never the secret key.
- `currency` is optional and defaults to the euro; `currency=` on a client sets another default.
- `void()` (type 9) and `payment_cancellation()` (type 45) on the direct clients, and `transactions.VOID`.
- Named operations on the direct clients: `authentication()`, `authentication_confirmation()`, `pay_gold()`, `authentication_confirmation_cancellation()` and `partial_confirmation()`.
- `inicia_payment()`, `inicia_preauthorization()` and `inicia_authentication()`, which default `emv3ds` to `threeds.card_data()`, and `challenge_response()` for the step after a 3DS challenge.
- `http_status`, `http_headers` and `raw_body` on `Response` and `ResponseError` after `send()`.
- `authentication()` (type 7) and `refund_without_original()` (type 34) on the redirect client, and `transactions.REDIRECT_TRANSACTION_TYPES`.
- `refund_without_original()` and `pay_gold_expiry_change()` (type 51, `transactions.PAY_GOLD_EXPIRY_CHANGE`) on the direct clients.
- `endpoint=` on every operation and `request()`: an HTTPS URL that replaces the client's for that request, never signed. `client.url(path)` joins the environment host and a path, and `redsys.environments` names the Bizum Request-to-Pay paths (`RTP_CHECK_PATH`, `RTP_TRATA_PATH`, `RTP_BACKUP_PATH`, `RTP_BACKUP_VALIDATION_PATH`).
- `docs/official-libraries.md`: equivalences for PHP and Java integrators.

### Changed

- `client.endpoint`, `inicia_endpoint` and the `REAL_ENDPOINT` / `TEST_ENDPOINT` class constants stay readable, but endpoints now resolve from the environment: a subclass that overrides those constants no longer changes where requests go.
- A `Ds_Merchant_TransactionType` that differs from the operation raises `ValidationError`; before, it was signed and sent. On an operation method, a different `transaction_type` raises `ValidationError` instead of `TypeError`.
- `RedirectClient.request()` raises `ValidationError` for a transaction type other than 0, 1, 7 and 34, the ones the redirect connection accepts.

### Deprecated

- `cancellation()`: it keeps sending type 9 and goes away in 3.0. Use `void()`, or `payment_cancellation()` for type 45.

### Fixed

- A `merchant_code`, `terminal` or `transaction_type` passed by its wire name no longer leaves a stray key in the signed parameters.

### Security

- Requires `cryptography` 50 or later; earlier releases from 44 on are affected by CVE-2026-69247 (GHSA-g6cj-pr64-35w5) in PKCS#7 `EnvelopedData` decryption. python-redsys does not call that API; the floor keeps integrator environments off the vulnerable range.
- GitHub Actions are pinned to commit SHAs, workflows default to read-only `contents` permission, and checkouts do not persist the token.

## [2.1.0] - 2026-10-25

### Added

- Transaction types 11, 38 and 44 to 48 from RedSys's table, usable through `client.request()`; 45 to 47 build cancellation messages and 48 a confirmation.
- Dynamic currency conversion: `dcc` on direct requests (`Ds_Merchant_DCC`) and `Response.dcc` (`Ds_DCC`).
- Tokenization and credential-on-file fields (`identifier`, `cof_*`, `direct_payment`) on redirect requests, as the redirect reference documents.

### Security

- CI requires uv 0.13.4 or later and the release build pip 26.2.2 or later, the versions that stop trusting the compromised eMudhra intermediate CAs.

### Fixed

- `Response.card_number` reads redirect notifications, which name the field `Ds_Card_Number` (REST uses `Ds_CardNumber`); it was left in `model_extra`.
- `Response.amount` keeps the currency's decimals: 100 EUR minor units read as `1.00`, not `1`.

## [2.0.0] - 2026-10-25

2.0 is a rewrite with a new API; see [`docs/migration-1x-to-2x.md`](docs/migration-1x-to-2x.md). 1.x receives fixes until 2026-12-31.

### Added

- Direct connection (REST) with `DirectClient` and `AsyncDirectClient`; `send()` needs the optional `http` extra (`httpx`).
- 3-D Secure v2: `inicia()`, the `redsys.threeds` builders and the 3DS accessors on `Response`.
- Signature versions `HMAC_SHA512_V2` and `HMAC_SHA512_V1`, alongside the legacy `HMAC_SHA256_V1`.
- Tokenization and recurring payments (COF/MIT), inSite tokens (`idoper`), Bizum on the redirect connection and the PSD2 SCA exemption (`excep_sca`, `redsys.sca`).
- Response fields for language, card typology, ECI, response description, Bizum, DCC, amount in euros and processed payment method. Parameters the library does not list are kept in `Response.model_extra`.
- Reference documents for both connections, response codes and the migration from 1.x; `SECURITY.md`, `CONTRIBUTING.md` and `CONTRIBUTORS.md`.
- Type hints (`py.typed`), CI on Python 3.10 to 3.15, and opt-in live tests against the RedSys test environment.

### Changed

- **Breaking:** new API. The client holds the account identity; `payment()`, `preauthorization()`, `confirmation()`, `refund()` and `cancellation()` return a signed `Request` (`to_dict()` or `send()`), and `parse_response()` verifies and parses. The module is `redsys.clients` (was `redsys.client`).
- **Breaking:** requests are Pydantic models validated on construction. A 1.x or misspelled field name raises `ValidationError`; an unmodeled `Ds_Merchant_*` wire name is sent as given with an `UnknownParameterWarning`.
- **Breaking:** response predicates are methods (`is_paid()`), `code` is `response_code`, and the Spanish `message` is gone; meanings are in `docs/response-codes.md`.
- **Breaking:** Python 3.10 or later; `cryptography` and `pydantic` replace `pycryptodome`.
- The default signature version is `HMAC_SHA512_V2`.
- Relicensed from MIT to Apache-2.0.

### Fixed

- Amounts scale by the currency's minor-unit exponent: JPY and CLP amounts are no longer multiplied by 100.

### Security

- Response signatures are compared in constant time.
- Releases are published to PyPI through Trusted Publishing, with attestations.

## [1.2.2] - 2026-10-17

### Fixed

- `Response.message` no longer raises `KeyError` for the 4-digit response codes RedSys sends (for example `0190`, `0900` or `0400`); a code without a description reads as `None`.

### Security

- PyCryptodome 3.19.1 or later is required, so an installation cannot resolve to a release affected by CVE-2023-52323 (side-channel leakage in RSA-OAEP decryption). The library only uses DES3 and does not reach the affected code.

## [1.2.1] - 2026-10-04

### Fixed

- `Request` and `Response` instances no longer share their parameters within a process: a parsed response could carry fields of a previously parsed one (for example its amount), and a request could carry fields of a previous request (for example the Bizum mobile number). Known parameters that are absent now read as `None`.

## [1.2.0] - 2023-10-28

### Added

- BIZUM payment option: `mobile_number` (`Ds_Merchant_Bizum_MobileNumber`) and `payment_method` (`Ds_Merchant_PayMethods`) request parameters.

### Changed

- Order IDs are validated as 12 characters (4 digits followed by 8 alphanumerics) instead of 9.

## [1.1.1] - 2022-01-06

### Fixed

- Responses no longer fail when RedSys adds parameters the library does not list; unlisted parameters are kept under their original key.

## [1.1.0] - 2021-10-19

### Changed

- `Response.parameters` exposes the decoded response parameters.

## [1.0.3] - 2021-09-21

### Fixed

- `Ds_Amount_Euro` parameter added to the response.

## [1.0.2] - 2021-03-24

### Fixed

- The secret key is a mandatory parameter.
- Minimum Python is 3.7.
- License file corrected.
- Code and message improvements, thanks @jdelarubia.

## [1.0.1] - 2020-12-30

### Fixed

- Required Python version.

## [1.0.0] - 2020-12-30

### Added

- Type hints checked with mypy.
- Request and response tests.

### Changed

- Requests are initialized with a dictionary of parameters.
- A response's code and message are available as `response.code` and `response.message`.
- `is_paid`, `is_refunded`, `is_canceled` and `is_authorized` are properties instead of methods.
- Static helpers are `@staticmethod`.

### Fixed

- The abstract client class is enforced.

## [0.4.0] - 2020-12-28

### Added

- Client tests.

### Changed

- pycrypto (abandoned) replaced by PyCryptodome.
- Currencies, languages and transaction types consolidated into a single constants module.
- Python 2 support dropped.

## [0.3.0] - 2020-12-26

### Changed

- Packaging migrated to Poetry, with pre-commit, isort and Black.
