from apps.audit.models import AuditLog, AuditAction


def get_client_ip(request):
    """Extrae la IP real del cliente considerando proxies."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_action(user, action, entity="", entity_id="", request=None, metadata=None):
    """
    Registra sistemáticamente un evento en AuditLog.
    """
    ip_address = get_client_ip(request) if request else None
    user_obj = user if (user and getattr(user, "is_authenticated", False)) else None

    return AuditLog.objects.create(
        user=user_obj,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id else "",
        ip_address=ip_address,
        metadata=metadata or {},
    )
