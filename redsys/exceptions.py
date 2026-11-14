class RedsysError(Exception):
    """Base class for redsys errors."""


class ResponseError(RedsysError):
    """RedSys returned an error payload instead of a signed result."""

    def __init__(self, error_code, payload=None):
        self.error_code = error_code
        self.payload = payload
        self.http_status = None
        self.http_headers = None
        self.raw_body = None
        super().__init__(f'RedSys returned error: {error_code}')


class ValidationError(RedsysError, ValueError):
    """Rejected input: a client option or operation fields RedSys does not accept, or a malformed received payload."""


class UnknownParameterWarning(UserWarning):
    """A request carries a RedSys wire-name parameter this library version does not model; it is sent as given."""
