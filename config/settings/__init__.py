import os

env = os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.development")

if "development" in env:
    from .development import *
elif "production" in env:
    from .production import *
elif "testing" in env:
    from .testing import *
else:
    from .base import *
