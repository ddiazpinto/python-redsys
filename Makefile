# Code style
# ------------------------------------------------------------------------------
check:
	poetry run isort . --profile black --check-only
	poetry run black . --check
	poetry run mypy .

format:
	poetry run isort . --profile black
	poetry run black .

# Create a new version
# ------------------------------------------------------------------------------
version-patch:
	poetry run semantic-release publish --patch

version-minor:
	poetry run semantic-release publish --minor

version-major:
	poetry run semantic-release publish --major
