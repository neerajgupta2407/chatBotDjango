import logging

from .base import *

# Testing settings
DEBUG = True

# Use in-memory SQLite for faster testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Password hashers (use faster hashers for testing)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Cache Configuration (use dummy cache for testing)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable logging during tests
LOGGING_CONFIG = None
logging.disable(logging.CRITICAL)

# CORS Configuration (allow all origins in testing)
CORS_ALLOW_ALL_ORIGINS = True
