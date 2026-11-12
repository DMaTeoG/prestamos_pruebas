from django.db import models
from apps.companies.models import CompanyProfile


class DataSourceSnapshot(models.Model):
    company = models.ForeignKey(
        CompanyProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="snapshots",
        verbose_name="Empresa",
    )
    nit = models.CharField("NIT Consultado", max_length=20, db_index=True)
    source_name = models.CharField("Fuente de Datos", max_length=50)
    status_code = models.IntegerField("Código HTTP", default=200)
    payload = models.JSONField("Respuesta Cruda (JSON)", default=dict, blank=True)
    fetched_at = models.DateTimeField("Fecha de Consulta", auto_now_add=True)

    class Meta:
        verbose_name = "Snapshot de Fuente de Datos"
        verbose_name_plural = "Snapshots de Fuentes de Datos"
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"[{self.source_name}] NIT {self.nit} - HTTP {self.status_code} ({self.fetched_at.strftime('%Y-%m-%d %H:%M')})"
