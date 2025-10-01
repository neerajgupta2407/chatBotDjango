from .base import *

# Development settings
DEBUG = True

# Database
DATABASES = {"default": env.db(default="sqlite:///" + str(BASE_DIR / "db.sqlite3"))}

# Email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
