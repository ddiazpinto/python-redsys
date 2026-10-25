.PHONY: test live

test:
	uv run pytest -q tests/

# Tests against the RedSys test environment; needs network access.
live:
	REDSYS_LIVE=1 uv run --extra http pytest -q tests/test_live.py
