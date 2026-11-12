import os
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse


def health_check(request):
    """Lightweight healthcheck endpoint for Docker, CD rollback, and Locust."""
    db_ok = True
    try:
        connections["default"].cursor()
    except OperationalError:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "database": "up" if db_ok else "down",
            "version": os.getenv("APP_VERSION", "dev"),
        },
        status=status_code,
    )
