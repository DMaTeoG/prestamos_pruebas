from rest_framework import generics
from apps.accounts.permissions import IsAdminUserRole
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer


class AdminAuditLogListView(generics.ListAPIView):
    """GET /api/v1/admin/audit/ — Lista el registro de auditoría (solo Administrador)."""

    permission_classes = [IsAdminUserRole]
    serializer_class = AuditLogSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user").all().order_by("-created_at")
        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action.strip().upper())
        return queryset[:100]
