class RedsysError(Exception):
    """Base class for redsys errors."""


class ResponseError(RedsysError):
    """RedSys returned an error payload instead of a signed result."""

    def __init__(self, error_code, payload=None):
        self.error_code = error_code
        self.payload = payload
        super().__init__(f'RedSys returned error: {error_code}')


class ValidationError(RedsysError):
    """A parameter failed validation."""


class UnknownParameterWarning(UserWarning):
    """A request carries a RedSys wire-name parameter this library version does not model; it is sent as given."""
