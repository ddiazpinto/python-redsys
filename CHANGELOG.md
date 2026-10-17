# Changelog

All notable changes to this project. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with [Semantic Versioning](https://semver.org/).

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
