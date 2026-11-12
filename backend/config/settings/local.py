import os
import sys

from .base import *  # noqa: F403

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Development email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if "pytest" in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
