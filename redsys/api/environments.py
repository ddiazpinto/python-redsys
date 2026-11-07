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
