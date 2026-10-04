# Create a new version
# ------------------------------------------------------------------------------
version-patch:
	poetry run semantic-release publish --patch

version-minor:
	poetry run semantic-release publish --minor

version-major:
	poetry run semantic-release publish --major
