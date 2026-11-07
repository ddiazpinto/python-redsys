"""Clients for the RedSys redirect and direct connections.

A client holds the credentials and the account (secret key, merchant code, terminal,
environment, signature version) and builds every operation as a signed ``Request``:

    client = DirectClient(secret_key='...', merchant_code='999008881', terminal=1, sandbox=True)
    response = client.payment(order=generate_order(), amount=Decimal('10.56')).send()

A redirect request ends in ``to_dict()``, the form the browser posts; a direct request
ends in ``send()``. ``parse_response()`` verifies and parses a received result.
"""

from base64 import b64decode
from hmac import compare_digest
from logging import getLogger
from re import fullmatch, sub
from urllib.parse import urlsplit
from warnings import warn

from redsys import threeds
from redsys.api import environments, transactions
from redsys.crypto import (
    DEFAULT_SIGNATURE_VERSION,
    HMAC_SHA256_V1,
    HMAC_SHA512_V1,
    HMAC_SHA512_V2,
    SIGNATURE_VERSIONS,
    get_signer,
)
from redsys.exceptions import ResponseError, ValidationError
from redsys.models import (
    BaseRequest,
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

# Seconds; ``send(timeout=...)`` overrides it.
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


def _resolve_environment(environment: str | None, sandbox: bool | None) -> str:
    """The environment a client targets; ``sandbox`` means TEST when true and PROD when false."""
    implied = None if sandbox is None else environments.TEST if sandbox else environments.PROD
    if environment is None:
        return implied or environments.PROD
    if environment not in environments.HOSTS:
        raise ValidationError('environment is not valid.')
    if implied not in (None, environment):
        raise ValidationError('environment contradicts sandbox.')
    return environment


def _endpoint_option(fields: dict) -> str | None:
    """Pop a call's ``endpoint``, which is never signed; it must be an HTTPS URL."""
    endpoint = fields.pop('endpoint', None)
    if endpoint is None:
        return None
    parts = urlsplit(endpoint) if isinstance(endpoint, str) else None
    if parts is None or parts.scheme != 'https' or not parts.netloc:
        raise ValidationError('endpoint must be an https:// URL.')
    return endpoint


def _parse_api_key(api_key: str) -> tuple[str, str, int, str]:
    """Split an API key into (environment, merchant code, terminal, secret key).

    The format is ``<environment>_<Base64URL of merchant_terminal_secret>``, with
    or without padding. Failures raise outside any ``except`` block and name no
    detail, so neither the key nor its decoded secret reaches the traceback.
    """
    environment, _, payload = api_key.partition('_') if isinstance(api_key, str) else ('', '', '')
    payload = payload.rstrip('=')
    try:
        decoded = b64decode(payload + '=' * (-len(payload) % 4), b'-_', validate=True).decode('utf-8')
    except ValueError:
        decoded = ''
    fields = fullmatch(r'([0-9]{1,9})_([0-9]{1,3})_(.+)', decoded)
    if environment not in environments.HOSTS or fields is None:
        raise ValidationError('API key is not valid.')
    merchant_code, terminal, secret_key = fields.groups()
    return environment, merchant_code, int(terminal), secret_key


class Client:
    """Base client: credentials, account identity, request factory, response parsing."""

    REAL_ENDPOINT: str | None = None
    TEST_ENDPOINT: str | None = None
    _PATH: str | None = None

    #: Request model per transaction type; other types use ``_DEFAULT_MODEL``.
    _DEFAULT_MODEL: type | None = None
    _MODELS: dict[int, type] = {}
    #: The transaction types the connection accepts; ``None`` leaves the check to the model.
    _TRANSACTION_TYPES: tuple[int, ...] | None = None

    def __init__(
        self,
        secret_key: str,
        *,
        merchant_code: str | None = None,
        terminal: int | None = None,
        currency: int | None = None,
        sandbox: bool | None = None,
        environment: str | None = None,
        signature_version: str = DEFAULT_SIGNATURE_VERSION,
    ):
        self._secret_key = secret_key
        self.merchant_code = merchant_code
        self.terminal = terminal
        self.currency = currency
        self.environment = _resolve_environment(environment, sandbox)
        self.sandbox = self.environment != environments.PROD
        self.signature_version = signature_version
        self.endpoint = self.url(self._PATH) if self._PATH else None

    @classmethod
    def from_api_key(cls, api_key: str, **options):
        """Build a client from a RedSys API key, which carries the environment and the credentials.

        ``options`` are the remaining constructor options (``signature_version``).
        Raises ``ValidationError`` if the key is not valid.
        """
        environment, merchant_code, terminal, secret_key = _parse_api_key(api_key)
        return cls(secret_key, merchant_code=merchant_code, terminal=terminal, environment=environment, **options)

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}(merchant_code={self.merchant_code!r}, terminal={self.terminal!r}, '
            f'environment={self.environment!r}, signature_version={self.signature_version!r})'
        )

    def url(self, path: str) -> str:
        """The client's environment host followed by ``path``, e.g. ``environments.RTP_TRATA_PATH``."""
        if not isinstance(path, str) or not path.startswith('/'):
            raise ValidationError('path must start with "/".')
        return f'{environments.HOSTS[self.environment]}{path}'

    # == Request building ==
    def _inject(self, fields: dict) -> dict:
        """Merge the client's account defaults into a call's fields (call wins, by either name)."""
        data = dict(fields)
        for name in ('merchant_code', 'terminal', 'currency'):
            value = getattr(self, name)
            if value is not None and name not in data and BaseRequest.model_fields[name].alias not in data:
                data[name] = value
        return data

    def _model_for(self, transaction_type: int) -> type:
        model = self._MODELS.get(transaction_type, self._DEFAULT_MODEL)
        if model is None:
            raise NotImplementedError('This client defines no request model; use a concrete subclass.')
        return model

    def request(self, transaction_type: int, **fields) -> Request:
        """Build, validate and sign any operation by its transaction type.

        For the types without a method, such as ``transactions.REFUND_CANCELLATION``.
        Raises ``ValidationError`` if ``fields`` name a different transaction type, or if
        the connection does not accept it (the redirect connection takes
        ``transactions.REDIRECT_TRANSACTION_TYPES``). Every operation takes ``endpoint=``,
        an HTTPS URL that replaces the client's for that request only; it is not signed.
        """
        return self._operation(transaction_type, fields)

    def _operation(self, transaction_type: int, fields: dict, endpoint: str | None = None) -> Request:
        fields = dict(fields)
        override = _endpoint_option(fields)
        return self._prepare(self._message(transaction_type, fields), endpoint=override or endpoint)

    def _message(self, transaction_type: int, fields: dict):
        if self._TRANSACTION_TYPES is not None and transaction_type not in self._TRANSACTION_TYPES:
            raise ValidationError(f'transaction type {transaction_type} is not accepted by {type(self).__name__}.')
        data = self._inject(fields)
        for name in ('transaction_type', BaseRequest.model_fields['transaction_type'].alias):
            if str(data.pop(name, transaction_type)) != str(transaction_type):
                raise ValidationError(f'{name} contradicts the operation, transaction type {transaction_type}.')
        return self._model_for(transaction_type)(**data, transaction_type=transaction_type)

    def _prepare(self, model, endpoint: str | None = None) -> Request:
        return self._build_request(model, endpoint=endpoint or self.endpoint)

    def _build_request(
        self, model, signature_version: str | None = None, sender=None, endpoint: str | None = None
    ) -> Request:
        version = signature_version or self.signature_version
        signer = get_signer(self._secret_key, version)
        merchant_parameters = signer.encode_parameters(model.prepare_parameters())
        signature = signer.sign(model.get_order(), merchant_parameters)
        return Request(merchant_parameters, signature, version, sender=sender, endpoint=endpoint)

    # == Response parsing ==
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
        # A signed result always carries Ds_Order; without it, '' makes verification fail.
        expected = get_signer(self._secret_key, version).sign(response.get_order() or '', merchant_parameters)
        if not compare_digest(_normalize_signature(payload[SIGNATURE]), _normalize_signature(expected)):
            raise ValueError('Signature is not valid.')
        return response


class RedirectClient(Client):
    """Redirect connection: builds the signed form fields the browser posts to RedSys; performs no HTTP."""

    # Endpoints per the redirection guide 4.2 (RS.TE.CEL.MAN.0039).
    _PATH = environments.REDIRECT_PATH
    REAL_ENDPOINT = environments.HOSTS[environments.PROD] + _PATH
    TEST_ENDPOINT = environments.HOSTS[environments.TEST] + _PATH
    _DEFAULT_MODEL = RedirectPaymentMessage
    _MODELS = {transactions.PREAUTHORIZATION: RedirectPreauthorizationMessage}
    _TRANSACTION_TYPES = transactions.REDIRECT_TRANSACTION_TYPES

    def payment(self, **fields) -> Request:
        return self._operation(transactions.AUTHORIZATION, fields)

    def preauthorization(self, **fields) -> Request:
        return self._operation(transactions.PREAUTHORIZATION, fields)

    def authentication(self, **fields) -> Request:
        """Authenticate the cardholder and validate the card, with no hold (transaction type 7)."""
        return self._operation(transactions.AUTHENTICATION, fields)

    def refund_without_original(self, **fields) -> Request:
        """Credit the cardholder with no previous sale (transaction type 34)."""
        return self._operation(transactions.REFUND_WITHOUT_ORIGINAL, fields)


def _require_httpx():
    try:
        import httpx
    except ImportError as exc:
        raise ImportError('Sending requires httpx. Install with: pip install "python-redsys[http]".') from exc
    return httpx


_EMV3DS_WIRE_NAME = 'Ds_Merchant_EMV3DS'


class _DirectBase(Client):
    """Operations of the REST direct connection, independent of the HTTP transport."""

    # Endpoints per the REST guide 4.0.1 (RS.TE.CEL.MAN.0037).
    _PATH = environments.TRATA_PATH
    REAL_ENDPOINT = environments.HOSTS[environments.PROD] + _PATH
    TEST_ENDPOINT = environments.HOSTS[environments.TEST] + _PATH
    INICIA_REAL_ENDPOINT = environments.HOSTS[environments.PROD] + environments.INICIA_PATH
    INICIA_TEST_ENDPOINT = environments.HOSTS[environments.TEST] + environments.INICIA_PATH

    _DEFAULT_MODEL = DirectPaymentMessage
    _MODELS = {
        transactions.PREAUTHORIZATION: DirectPreauthorizationMessage,
        transactions.CONFIRMATION: ConfirmationMessage,
        transactions.REFUND: RefundMessage,
        transactions.VOID: CancellationMessage,
        transactions.REPLACEMENT_PREAUTHORIZATION: DirectPreauthorizationMessage,
        transactions.PARTIAL_CONFIRMATION: ConfirmationMessage,
        transactions.PAYMENT_CANCELLATION: CancellationMessage,
        transactions.REFUND_CANCELLATION: CancellationMessage,
        transactions.AUTHENTICATION_CONFIRMATION_CANCELLATION: CancellationMessage,
    }

    @property
    def inicia_endpoint(self) -> str:
        return self.url(environments.INICIA_PATH)

    def payment(self, **fields) -> Request:
        return self._operation(transactions.AUTHORIZATION, fields)

    def preauthorization(self, **fields) -> Request:
        return self._operation(transactions.PREAUTHORIZATION, fields)

    def confirmation(self, **fields) -> Request:
        return self._operation(transactions.CONFIRMATION, fields)

    def partial_confirmation(self, **fields) -> Request:
        return self._operation(transactions.PARTIAL_CONFIRMATION, fields)

    def authentication(self, **fields) -> Request:
        return self._operation(transactions.AUTHENTICATION, fields)

    def authentication_confirmation(self, **fields) -> Request:
        return self._operation(transactions.AUTHENTICATION_CONFIRMATION, fields)

    def authentication_confirmation_cancellation(self, **fields) -> Request:
        return self._operation(transactions.AUTHENTICATION_CONFIRMATION_CANCELLATION, fields)

    def pay_gold(self, **fields) -> Request:
        return self._operation(transactions.PAY_GOLD, fields)

    def pay_gold_expiry_change(self, **fields) -> Request:
        """Change the expiry of a PayGold link (transaction type 51); RedSys requires ``amount``."""
        return self._operation(transactions.PAY_GOLD_EXPIRY_CHANGE, fields)

    def refund_without_original(self, **fields) -> Request:
        """Credit the cardholder with no previous sale (transaction type 34)."""
        return self._operation(transactions.REFUND_WITHOUT_ORIGINAL, fields)

    def refund(self, **fields) -> Request:
        return self._operation(transactions.REFUND, fields)

    def void(self, **fields) -> Request:
        """Void a preauthorization (transaction type 9)."""
        return self._operation(transactions.VOID, fields)

    def payment_cancellation(self, **fields) -> Request:
        """Cancel a payment after a merchant time-out or technical error (transaction type 45)."""
        return self._operation(transactions.PAYMENT_CANCELLATION, fields)

    def cancellation(self, **fields) -> Request:
        """Deprecated: sends type 9; use ``void()``, or ``payment_cancellation()`` for type 45."""
        warn(
            'cancellation() is deprecated and goes away in 3.0: use void() for type 9, the type it sends, '
            'or payment_cancellation() for type 45.',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.void(**fields)

    def inicia(self, **fields) -> Request:
        """3-D Secure initialization (iniciaPeticionREST) from the given fields, ``emv3ds`` included."""
        fields = dict(fields)
        endpoint = _endpoint_option(fields)
        model = self._DEFAULT_MODEL(**self._inject(fields))
        return self._prepare(model, endpoint=endpoint or self.inicia_endpoint)

    def inicia_payment(self, **fields) -> Request:
        """3-D Secure step 1 for a payment; ``emv3ds`` defaults to ``threeds.card_data()``."""
        return self._inicia(transactions.AUTHORIZATION, fields)

    def inicia_preauthorization(self, **fields) -> Request:
        """3-D Secure step 1 for a preauthorization; ``emv3ds`` defaults to ``threeds.card_data()``."""
        return self._inicia(transactions.PREAUTHORIZATION, fields)

    def inicia_authentication(self, **fields) -> Request:
        """3-D Secure step 1 for an authentication; ``emv3ds`` defaults to ``threeds.card_data()``."""
        return self._inicia(transactions.AUTHENTICATION, fields)

    def _inicia(self, transaction_type: int, fields: dict) -> Request:
        if 'emv3ds' not in fields and _EMV3DS_WIRE_NAME not in fields:
            fields['emv3ds'] = threeds.card_data()
        return self._operation(transaction_type, fields, endpoint=self.inicia_endpoint)

    def challenge_response(
        self, *, cres: str, protocol_version: str, transaction_type: int = transactions.AUTHORIZATION, **fields
    ) -> Request:
        """3-D Secure final step after the challenge; ``transaction_type`` is the one authenticated."""
        if 'emv3ds' in fields or _EMV3DS_WIRE_NAME in fields:
            raise ValidationError('challenge_response() builds emv3ds from cres and protocol_version.')
        emv3ds = threeds.challenge_response(cres=cres, protocol_version=protocol_version)
        return self._operation(transaction_type, {**fields, 'emv3ds': emv3ds})

    def _prepare(self, model, endpoint: str | None = None) -> Request:
        return self._build_request(model, sender=self._send, endpoint=endpoint or self.endpoint)

    def _send(self, request, **httpx_kwargs):
        raise NotImplementedError

    def _parse_http_response(self, http_response) -> Response:
        http_response.raise_for_status()
        transport = (http_response.status_code, dict(http_response.headers), http_response.text)
        try:
            response = self.parse_response(http_response.json())
        except ResponseError as error:
            error.http_status, error.http_headers, error.raw_body = transport
            raise
        return response._with_transport(*transport)


class DirectClient(_DirectBase):
    """Synchronous REST direct-connection client; ``send()`` requires the ``http`` extra (httpx)."""

    def _send(self, request, **httpx_kwargs):
        httpx = _require_httpx()
        httpx_kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        return self._parse_http_response(httpx.post(request.endpoint, json=request.to_dict(), **httpx_kwargs))


class AsyncDirectClient(_DirectBase):
    """Asynchronous REST direct-connection client; ``await send()`` requires the ``http`` extra (httpx)."""

    async def _send(self, request, **httpx_kwargs):
        httpx = _require_httpx()
        httpx_kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        async with httpx.AsyncClient() as client:
            http_response = await client.post(request.endpoint, json=request.to_dict(), **httpx_kwargs)
        return self._parse_http_response(http_response)
