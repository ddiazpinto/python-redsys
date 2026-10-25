# Contributing to python-redsys

`python-redsys` is a small client for the RedSys payment gateway: it prepares signed payloads and verifies and parses responses. Contributions that keep it that way are welcome.

## The lightweight rule

No new runtime dependencies and no HTTP or UI frameworks. The runtime dependencies are `cryptography` and `pydantic`; networking is limited to the optional `httpx` sender behind the `http` extra.

## Development setup

Python 3.10 or later and [uv](https://docs.astral.sh/uv/). `uv.lock` pins every development dependency with hashes; CI installs from it with `--locked`.

```bash
git clone https://github.com/ddiazpinto/python-redsys
cd python-redsys
uv sync --extra http
uv run pre-commit install
```

## Checks

CI runs these on Python 3.10 to 3.15, plus the test suite against the lowest declared dependency versions; all must pass before a merge.

```bash
uv run ruff check redsys tests
uv run ruff format --check redsys tests
uv run mypy redsys
uv run pytest -q
```

After changing dependencies in `pyproject.toml`, run `uv lock` and commit `uv.lock`.

- Style: ruff lint and format, line length 120, single quotes, type hints.
- New behavior needs tests. Signing and verification changes need known-answer vectors (see `tests/test_crypto.py`), not assertions against the implementation.

## Live tests

`tests/test_live.py` runs the direct connection end to end against the RedSys test environment with RedSys's public test merchant: 3DS initialization, a payment that requires SCA, a challenged payment through RedSys's simulator ACS, and a refund, once per signature version. It needs network access and runs only on request:

```bash
make live   # REDSYS_LIVE=1 uv run --extra http pytest -q tests/test_live.py
```

In GitHub Actions, run the *Live* workflow manually.

## Changing the models

The models live in `redsys/models.py`: one Pydantic class per message, each field declared with its RedSys wire name as the alias and the constraints of the integration guides listed in the module docstring. A new parameter is a field on the message (or on the shared redirect or direct field set), a test that checks its wire name and a changelog line. Endpoint URLs are in `redsys/clients.py`.

## Pull requests

- Branch from `master`; one change per pull request.
- User-visible changes get an entry under `## [Unreleased]` in `CHANGELOG.md` ([Keep a Changelog](https://keepachangelog.com/), SemVer).
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) and explain the why.

## License of contributions

The project is licensed under the Apache License 2.0. A contribution is provided under the same terms (section 5); its author keeps the copyright.
