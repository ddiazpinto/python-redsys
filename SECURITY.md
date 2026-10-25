# Security policy

`python-redsys` builds and verifies the signed messages exchanged with the RedSys TPV Virtual payment gateway. Reports are handled with priority.

## Supported versions

| Version | Status | Supported until |
|---------|--------|-----------------|
| 2.x | Active, all fixes | ongoing |
| 1.x | Security and critical fixes | 2026-12-31 |
| < 1.0 | End of life | n/a |

Fixes land on 2.x and are backported to 1.x while it is supported.

## Python versions

2.x supports CPython 3.10 and later, the versions its runtime dependencies support; 3.10 is the version Ubuntu 22.04 LTS ships. A Python version is dropped in a minor release, announced in the changelog, once `pydantic` or `cryptography` drop it.

## Reporting a vulnerability

Do not open a public issue. Report privately through GitHub: *Security*, then *Report a vulnerability*, on <https://github.com/ddiazpinto/python-redsys/security/advisories>, or email the maintainer listed in the package metadata.

Include the affected versions, the impact, a minimal reproduction (a failing signature or verification case is ideal) and any suggested fix. Reports are acknowledged within a few days; the fix is released in coordination with the reporter, who is credited with their permission.

## Security model

The library prepares signed request parameters and verifies and parses responses. It does not manage TLS, store secrets or render UI; the optional `httpx` sender is its only networking code. The integrator is responsible for:

- **Transport:** exchanging messages over TLS.
- **Secret key:** keeping the merchant secret out of source control, logs and error reports.
- **Verification:** acting only on responses returned by `client.parse_response()`, which raises on a signature mismatch and compares signatures in constant time.
- **Signature version:** using a SHA-512 version (`HMAC_SHA512_V2`, the default, or `HMAC_SHA512_V1`); `HMAC_SHA256_V1` (3DES) is legacy.
