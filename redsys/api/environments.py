"""RedSys environments and their hosts."""

DESA = 'DESA'
"""Development."""

INTE = 'INTE'
"""Integration."""

TEST = 'TEST'
"""Test."""

PROD = 'PROD'
"""Production."""

HOSTS = {
    DESA: 'https://sis-d.redsys.es',
    INTE: 'https://sis-i.redsys.es:25443',
    TEST: 'https://sis-t.redsys.es:25443',
    PROD: 'https://sis.redsys.es',
}

REDIRECT_PATH = '/sis/realizarPago'
INICIA_PATH = '/sis/rest/iniciaPeticionREST'
TRATA_PATH = '/sis/rest/trataPeticionREST'

RTP_CHECK_PATH = '/sis/rest/RTP/checkRtpUsuario'
"""Bizum Request-to-Pay: whether the customer can receive a payment request."""

RTP_TRATA_PATH = '/sis/rest/RTP/trataPeticionREST'
"""Bizum Request-to-Pay: payment (types 0 and 7) and refund without original (type 34)."""

RTP_BACKUP_PATH = '/sis/rest/RTP/respaldarUsuarioRTP'
"""Bizum Request-to-Pay backup: starts it and sends the customer a one-time password."""

RTP_BACKUP_VALIDATION_PATH = '/sis/rest/RTP/validarRespaldoUsuarioRTP'
"""Bizum Request-to-Pay backup: validates the one-time password."""
