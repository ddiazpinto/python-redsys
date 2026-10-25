"""Client entry points for the RedSys platform.

The client is the single entry point: it holds the credentials and account
identity (secret key, merchant code, terminal, signature version) and acts as
the factory for every operation. You never build or import a request model --
call an operation method (``payment``, ``refund``, ...) or the low-level
``request()`` they all delegate to, and you get back a ``Request``:

    client = DirectClient(secret_key='...', merchant_code='...', terminal=1, sandbox=True)
    response = client.payment(order='000000001', amount=Decimal('10.56'), currency=978).send()

Redirect requests end in ``.to_dict()`` (the browser submits them); direct
requests end in ``.send()`` (the library performs the REST call). Both verify
and parse incoming results through ``client.parse_response(payload)``.
"""

from hmac import compare_digest
from logging import getLogger
from re import sub

from redsys.api import transactions
from redsys.crypto import (
    DEFAULT_SIGNATURE_VERSION,
    HMAC_SHA256_V1,
    HMAC_SHA512_V1,
    HMAC_SHA512_V2,
    SIGNATURE_VERSIONS,
    get_signer,
)
from redsys.exceptions import ResponseError
from redsys.models import (
    CancellationMessage,
    ConfirmationMessage,
    DirectPaymentMessage,
    DirectPreauthorizationMessage,
    RedirectPaymentMessage,
    RedirectPreauthorizationMessage,
    RefundMessage,
    Response,
)
from redsys.request import (
    MERCHANT_PARAMETERS,
    SIGNATURE,
    SIGNATURE_VERSION,
    Request,
)

logger = getLogger(__name__)

# Default HTTP timeout (seconds) for direct-connection network calls; override per call.
DEFAULT_TIMEOUT = 30

__all__ = [
    'Client',
    'RedirectClient',
    'DirectClient',
    'AsyncDirectClient',
    'Request',
    'SIGNATURE_VERSION',
    'MERCHANT_PARAMETERS',
    'SIGNATURE',
    'HMAC_SHA256_V1',
    'HMAC_SHA512_V1',
    'HMAC_SHA512_V2',
    'SIGNATURE_VERSIONS',
    'DEFAULT_SIGNATURE_VERSION',
]


def _normalize_signature(signature) -> str:
    """Reduce a signature to its alphanumeric core for comparison.

    RedSys returns response signatures in URL-safe Base64 ('-', '_') while
    standard Base64 uses ('+', '/'). Comparing only the alphanumeric characters
    makes the two alphabets and any padding compare equal.
    """
    if isinstance(signature, bytes):
        signature = signature.decode('utf-8')
    return sub(r'[^a-zA-Z0-9]', '', signature)


class Client:
    """Base client: credentials, account identity, request factory, response parsing."""

    REAL_ENDPOINT: str | None = None
    TEST_ENDPOINT: str | None = None

    #: transaction_type -> request model. Unmapped types fall back to _DEFAULT_MODEL.
    _DEFAULT_MODEL: type | None = None
    _MODELS: dict[int, type] = {}

    def __init__(
        self,
        secret_key: str,
        *,
        merchant_code: str | None = None,
        terminal: int | None = None,
        sandbox: bool = False,
        signature_version: str = DEFAULT_SIGNATURE_VERSION,
    ):
        self._secret_key = secret_key
        self.merchant_code = merchant_code
        self.terminal = terminal
        self.sandbox = sandbox
        self.signature_version = signature_version
        self.endpoint = self.TEST_ENDPOINT if sandbox else self.REAL_ENDPOINT

    # -- request building -------------------------------------------------
    def _inject(self, fields: dict) -> dict:
        """Merge the client's account identity into a call's fields (call wins)."""
        data: dict = {}
        if self.merchant_code is not None:
            data['merchant_code'] = self.merchant_code
        if self.terminal is not None:
            data['terminal'] = self.terminal
        data.update(fields)
        return data

    def _model_for(self, transaction_type: int) -> type:
        model = self._MODELS.get(transaction_type, self._DEFAULT_MODEL)
        if model is None:
            raise NotImplementedError('This client defines no request model; use a concrete subclass.')
        return model

    def request(self, transaction_type: int, **fields) -> Request:
        """Build, validate and sign any operation by its transaction type.

        The single funnel every named operation delegates to. Use it directly
        for transaction types without a dedicated method (e.g. ``PAY_GOLD``).
        """
        data = self._inject(fields)
        data.setdefault('transaction_type', transaction_type)
        model = self._model_for(transaction_type)(**data)
        return self._prepare(model)

    def _prepare(self, model) -> Request:
        return self._build_request(model)

    def _build_request(self, model, signature_version: str | None = None, sender=None) -> Request:
        version = signature_version or self.signature_version
        signer = get_signer(self._secret_key, version)
        merchant_parameters = signer.encode_parameters(model.prepare_parameters())
        signature = signer.sign(model.get_order(), merchant_parameters)
        return Request(merchant_parameters, signature, version, sender=sender)

    # -- response ---------------------------------------------------------
    def parse_response(self, payload: dict) -> Response:
        """Verify the signature and parse a received payload into a ``Response``.

        Accepts both the redirect callback form fields and the direct REST JSON
        body. Raises ``ValueError`` if the signature does not match (the payload
        is not from RedSys or was tampered with), or ``ResponseError`` if RedSys
        answered with an error code instead of a signed result.
        """
        if MERCHANT_PARAMETERS not in payload:
            error_code = payload.get('errorCode') or payload.get('Ds_ErrorCode')
            raise ResponseError(error_code, payload)
        merchant_parameters = payload[MERCHANT_PARAMETERS]
        if isinstance(merchant_parameters, str):
            merchant_parameters = merchant_parameters.encode('utf-8')
        version = payload.get(SIGNATURE_VERSION, DEFAULT_SIGNATURE_VERSION)
        response = Response.from_merchant_parameters(merchant_parameters)
        # A signed result always carries Ds_Order; '' can never match, so a
        # missing order simply fails verification below.
        expected = get_signer(self._secret_key, version).sign(response.get_order() or '', merchant_parameters)
        # Constant-time comparison to avoid leaking the signature via timing.
        if not compare_digest(_normalize_signature(payload[SIGNATURE]), _normalize_signature(expected)):
            raise ValueError('Signature is not valid.')
        return response


class RedirectClient(Client):
    """Redirect connection (secure method): builds the signed POST parameters the
    browser submits to RedSys. The library performs no HTTP and no redirect."""

    # Endpoints per the redirection guide 4.2 (RS.TE.CEL.MAN.0039).
    REAL_ENDPOINT = 'https://sis.redsys.es/sis/realizarPago'
    TEST_ENDPOINT = 'https://sis-t.redsys.es:25443/sis/realizarPago'
    _DEFAULT_MODEL = RedirectPaymentMessage
    _MODELS = {transactions.PREAUTHORIZATION: RedirectPreauthorizationMessage}

    def payment(self, **fields) -> Request:
        return self.request(transactions.AUTHORIZATION, **fields)

    def preauthorization(self, **fields) -> Request:
        return self.request(transactions.PREAUTHORIZATION, **fields)


def _require_httpx():
    try:
        import httpx
    except ImportError as exc:
        raise ImportError('Sending requires httpx. Install with: pip install "python-redsys[http]".') from exc
    return httpx


class _DirectBase(Client):
    """Shared REST direct-connection logic (transport-agnostic)."""

    # Endpoints per the REST guide 4.0.1 (RS.TE.CEL.MAN.0037).
    REAL_ENDPOINT = 'https://sis.redsys.es/sis/rest/trataPeticionREST'
    TEST_ENDPOINT = 'https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST'
    INICIA_REAL_ENDPOINT = 'https://sis.redsys.es/sis/rest/iniciaPeticionREST'
    INICIA_TEST_ENDPOINT = 'https://sis-t.redsys.es:25443/sis/rest/iniciaPeticionREST'

    _DEFAULT_MODEL = DirectPaymentMessage
    _MODELS = {
        transactions.PREAUTHORIZATION: DirectPreauthorizationMessage,
        transactions.CONFIRMATION: ConfirmationMessage,
        transactions.REFUND: RefundMessage,
        transactions.CANCELLATION: CancellationMessage,
        transactions.REPLACEMENT_PREAUTHORIZATION: DirectPreauthorizationMessage,
        transactions.PARTIAL_CONFIRMATION: ConfirmationMessage,
        transactions.PAYMENT_CANCELLATION: CancellationMessage,
        transactions.REFUND_CANCELLATION: CancellationMessage,
        transactions.AUTHENTICATION_CONFIRMATION_CANCELLATION: CancellationMessage,
    }

    @property
    def inicia_endpoint(self) -> str:
        return self.INICIA_TEST_ENDPOINT if self.sandbox else self.INICIA_REAL_ENDPOINT

    def payment(self, **fields) -> Request:
        return self.request(transactions.AUTHORIZATION, **fields)

    def preauthorization(self, **fields) -> Request:
        return self.request(transactions.PREAUTHORIZATION, **fields)

    def confirmation(self, **fields) -> Request:
        return self.request(transactions.CONFIRMATION, **fields)

    def refund(self, **fields) -> Request:
        return self.request(transactions.REFUND, **fields)

    def cancellation(self, **fields) -> Request:
        return self.request(transactions.CANCELLATION, **fields)

    def inicia(self, **fields) -> Request:
        """3-D Secure step 1: build a request bound to the iniciaPeticionREST endpoint."""
        model = self._DEFAULT_MODEL(**self._inject(fields))
        return self._prepare(model, endpoint=self.inicia_endpoint)

    def _prepare(self, model, endpoint: str | None = None) -> Request:
        endpoint = endpoint or self.endpoint
        return self._build_request(model, sender=self._make_sender(endpoint))

    def _make_sender(self, endpoint):
        raise NotImplementedError


class DirectClient(_DirectBase):
    """Synchronous REST direct-connection client. Requires the httpx extra."""

    def _make_sender(self, endpoint):
        def sender(request, **httpx_kwargs):
            httpx = _require_httpx()
            httpx_kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
            http_response = httpx.post(endpoint, json=request.to_dict(), **httpx_kwargs)
            http_response.raise_for_status()
            return self.parse_response(http_response.json())

        return sender


class AsyncDirectClient(_DirectBase):
    """Asynchronous REST direct-connection client (httpx.AsyncClient). Requires the httpx extra."""

    def _make_sender(self, endpoint):
        async def sender(request, **httpx_kwargs):
            httpx = _require_httpx()
            httpx_kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
            async with httpx.AsyncClient() as client:
                http_response = await client.post(endpoint, json=request.to_dict(), **httpx_kwargs)
            http_response.raise_for_status()
            return self.parse_response(http_response.json())

        return sender
