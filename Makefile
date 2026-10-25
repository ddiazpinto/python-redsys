.PHONY: test lock

# Interpreter to use; override if the venv is not activated, e.g.
#   make test PYTHON=.venv/bin/python
PYTHON ?= python

test:
	$(PYTHON) -m pytest -q tests/

# Regenerate the hash-pinned lint/type lock (runtime deps + ruff + mypy).
lock:
	$(PYTHON) -m piptools compile --generate-hashes \
		--extra lint \
		--output-file requirements-lint.lock pyproject.toml
