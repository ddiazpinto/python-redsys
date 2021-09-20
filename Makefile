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
version:
	poetry run semantic-release publish
