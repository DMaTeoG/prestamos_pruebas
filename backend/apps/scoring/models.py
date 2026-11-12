from django.conf import settings
from django.db import models

from apps.companies.models import CompanyProfile
from apps.financials.models import FinancialStatement


class RiskLevel(models.TextChoices):
    BAJO = "BAJO", "Bajo Riesgo (750 - 1000)"
    MEDIO = "MEDIO", "Riesgo Medio (500 - 749)"
    ALTO = "ALTO", "Alto Riesgo (250 - 499)"
    MUY_ALTO = "MUY_ALTO", "Muy Alto Riesgo (0 - 249)"


class CreditDecisionStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente de Comité"
    APPROVED = "APPROVED", "Aceptado por Comité"
    REJECTED = "REJECTED", "Rechazado por Comité"


class ModelVersion(models.Model):
    version = models.CharField("Versión del Modelo", max_length=50, unique=True)
    algorithm = models.CharField("Algoritmo", max_length=100)
    features = models.JSONField("Vector de Features", default=list)
    metrics = models.JSONField("Métricas de Rendimiento", default=dict)
    dataset_hash = models.CharField("Hash del Dataset", max_length=64, blank=True)
    artifact_path = models.CharField("Ruta al Artefacto .joblib", max_length=255)
    is_active = models.BooleanField("Modelo Activo", default=False)
    trained_at = models.DateTimeField("Fecha de Entrenamiento", auto_now_add=True)

    class Meta:
        verbose_name = "Versión de Modelo ML"
        verbose_name_plural = "Versiones de Modelos ML"
        ordering = ["-trained_at"]

    def __str__(self):
        active_str = " (ACTIVO)" if self.is_active else ""
        return f"{self.version} - {self.algorithm}{active_str}"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Desactivar otras versiones activas
            ModelVersion.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Evaluation(models.Model):
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name="Empresa Evaluada",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name="Solicitado por",
    )
    statement = models.ForeignKey(
        FinancialStatement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evaluations",
        verbose_name="Estado Financiero Usado",
    )
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.PROTECT,
        related_name="evaluations",
        verbose_name="Versión del Modelo",
    )
    pd = models.FloatField("Probabilidad de Incumplimiento (PD)")
    score = models.IntegerField("Score Crediticio (0-1000)")
    risk_level = models.CharField("Nivel de Riesgo", max_length=20, choices=RiskLevel.choices)
    confidence = models.CharField("Confianza del Resultado", max_length=20, default="ALTA")
    factors = models.JSONField("Factores de Riesgo SHAP (Top 5)", default=list)
    inputs_snapshot = models.JSONField("Snapshot Inmutable de Inputs", default=dict)
    requested_amount = models.DecimalField(
        "Monto Solicitado (COP)",
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    term_months = models.PositiveIntegerField(
        "Plazo Solicitado (Meses)",
        null=True,
        blank=True,
    )
    decision_status = models.CharField(
        "Decisión Manual de Comité",
        max_length=20,
        choices=CreditDecisionStatus.choices,
        default=CreditDecisionStatus.PENDING,
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_evaluations",
        verbose_name="Decidido por",
    )
    decided_at = models.DateTimeField("Fecha de Decisión", null=True, blank=True)
    created_at = models.DateTimeField("Fecha de Evaluación", auto_now_add=True)

    class Meta:
        verbose_name = "Evaluación Crediticia"
        verbose_name_plural = "Evaluaciones Crediticias"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Evaluación #{self.id} - NIT {self.company.nit}: Score {self.score} ({self.get_risk_level_display()})"
