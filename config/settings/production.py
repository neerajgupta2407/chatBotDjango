from .base import *

# Production settings
DEBUG = False

# Database
DATABASES = {"default": env.db()}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
