# Wire field names of the request/response envelope.
SIGNATURE_VERSION = 'Ds_SignatureVersion'
MERCHANT_PARAMETERS = 'Ds_MerchantParameters'
SIGNATURE = 'Ds_Signature'


def _as_text(value):
    return value.decode('utf-8') if isinstance(value, (bytes, bytearray)) else value


class Request:
    """A signed request, ready to serialize or send -- the return of every operation.

    Holds the three fields RedSys exchanges (the Base64 merchant parameters, the
    signature over them, and the signature version) and the two ways to hand it
    off:

    - ``to_dict()`` -- the three ``Ds_*`` fields to POST (redirect form fields or
      REST JSON body). Always available.
    - ``send()`` -- performs the REST call and returns the parsed ``Response``.
      Only direct-connection clients bind a sender; for redirect requests (the
      browser submits them) it raises ``TypeError`` -- use ``to_dict()``.

    Async clients bind an awaitable sender, so ``await request.send()`` works.
    """

    def __init__(self, merchant_parameters: bytes, signature: bytes, signature_version: str, *, sender=None):
        self._merchant_parameters = merchant_parameters
        self._signature = signature
        self._signature_version = signature_version
        self._sender = sender

    @property
    def merchant_parameters(self) -> bytes:
        return self._merchant_parameters

    @property
    def signature(self) -> bytes:
        return self._signature

    @property
    def signature_version(self) -> str:
        return self._signature_version

    def to_dict(self) -> dict:
        """The three wire fields (``Ds_SignatureVersion`` / ``Ds_MerchantParameters`` / ``Ds_Signature``)."""
        return {
            SIGNATURE_VERSION: self._signature_version,
            MERCHANT_PARAMETERS: _as_text(self._merchant_parameters),
            SIGNATURE: _as_text(self._signature),
        }

    def send(self, **httpx_kwargs):
        """Perform the direct (REST) call and return the parsed ``Response``.

        Raises ``TypeError`` for redirect requests, which the browser submits;
        use ``to_dict()`` to get their POST parameters instead.
        """
        if self._sender is None:
            raise TypeError(
                'Redirect requests are submitted by the browser; call to_dict() to obtain the POST parameters.'
            )
        return self._sender(self, **httpx_kwargs)
