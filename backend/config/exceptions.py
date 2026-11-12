import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("scoring.api")


def custom_exception_handler(exc, context):
    """
    Global DRF exception handler that logs errors for traceability without
    leaking sensitive tokens or passwords, and normalizes error payloads.
    """
    request = context.get("request")
    view = context.get("view")
    method = getattr(request, "method", "UNKNOWN")
    path = getattr(request, "path", "UNKNOWN")
    view_name = view.__class__.__name__ if view else "UnknownView"

    response = exception_handler(exc, context)

    if response is None:
        logger.error(
            "Unhandled server exception in %s [%s %s]: %s",
            view_name,
            method,
            path,
            exc.__class__.__name__,
            exc_info=True,
        )
        return Response(
            {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Ocurrió un error interno en el servidor.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    status_code = response.status_code
    if status_code >= 500:
        logger.error(
            "API 5xx error (%s) in %s [%s %s]: %s",
            status_code,
            view_name,
            method,
            path,
            exc.__class__.__name__,
        )
    else:
        logger.warning(
            "API %s response in %s [%s %s]: %s",
            status_code,
            view_name,
            method,
            path,
            exc.__class__.__name__,
        )

    if isinstance(response.data, dict):
        if "code" not in response.data:
            default_code = getattr(exc, "default_code", "API_ERROR")
            response.data["code"] = str(default_code).upper()
        if "message" not in response.data:
            detail = response.data.get("detail")
            if detail:
                response.data["message"] = str(detail)
            else:
                response.data["message"] = "Error de validación en la solicitud."

    return response
