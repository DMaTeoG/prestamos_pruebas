from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    SEARCH_NIT = "SEARCH_NIT", "Consulta de NIT"
    EVALUATION_REQUEST = "EVALUATION_REQUEST", "Solicitud de Evaluación"
    CREDIT_DECISION = "CREDIT_DECISION", "Decisión Manual de Comité"
    REPORT_DOWNLOAD = "REPORT_DOWNLOAD", "Descarga de Informe PDF"
    FINANCIAL_STATEMENT_UPLOAD = "FINANCIAL_STATEMENT_UPLOAD", "Carga de Estados Financieros"
    MEMBERSHIP_APPROVAL = "MEMBERSHIP_APPROVAL", "Aprobación de Vínculo"
    MODEL_ACTIVATION = "MODEL_ACTIVATION", "Activación de Modelo ML"
    USER_LOGIN = "USER_LOGIN", "Inicio de Sesión"


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="Usuario",
    )
    action = models.CharField("Acción", max_length=100, choices=AuditAction.choices)
    entity = models.CharField("Entidad Afectada", max_length=100, blank=True)
    entity_id = models.CharField("ID de Entidad", max_length=100, blank=True)
    ip_address = models.GenericIPAddressField("Dirección IP", null=True, blank=True)
    metadata = models.JSONField("Metadatos Adicionales", default=dict, blank=True)
    created_at = models.DateTimeField("Fecha y Hora", auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.email if self.user else "Anónimo/Sistema"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.get_action_display()}"
