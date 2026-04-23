from urllib.parse import urlparse

from .base import *
from decouple import config, Csv


def _normalize_host(value):
    value = (value or '').strip()
    if not value:
        return ''
    if '://' in value:
        parsed = urlparse(value)
        return parsed.netloc.strip()
    return value.strip().strip('/')


def _normalize_origin(value):
    value = (value or '').strip()
    if not value:
        return ''
    if '://' in value:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            return f'{parsed.scheme}://{parsed.netloc}'
        return ''
    host = value.strip().strip('/')
    return f'https://{host}'

DEBUG = False

_configured_allowed_hosts = config(
    'ALLOWED_HOSTS',
    default='sgti.onrender.com,sgti.cmgprod.com.br,www.sgti.cmgprod.com.br,.onrender.com,localhost,127.0.0.1',
    cast=Csv(),
)
ALLOWED_HOSTS = [
    host for host in (_normalize_host(value) for value in _configured_allowed_hosts) if host
]
APP_BASE_URL = config('APP_BASE_URL', default='https://sgti.onrender.com')
_configured_csrf_origins = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://sgti.onrender.com,https://sgti.cmgprod.com.br,https://www.sgti.cmgprod.com.br',
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = [
    origin for origin in (_normalize_origin(value) for value in _configured_csrf_origins) if origin
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
