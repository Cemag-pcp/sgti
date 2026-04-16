from .base import *
from decouple import config, Csv

DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='sgti.onrender.com,.onrender.com,localhost,127.0.0.1',
    cast=Csv(),
)
APP_BASE_URL = config('APP_BASE_URL', default='https://sgti.onrender.com')

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
