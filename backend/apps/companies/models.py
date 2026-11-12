from django.db import models
from django.conf import settings


class CompanySize(models.TextChoices):
    MICRO = "MICRO", "Microempresa"
    PEQUENA = "PEQUENA", "Pequeña Empresa"
    MEDIANA = "MEDIANA", "Mediana Empresa"
    GRANDE = "GRANDE", "Gran Empresa"


class MembershipStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    APPROVED = "APPROVED", "Aprobado"
    REJECTED = "REJECTED", "Rechazado"


class CompanyProfile(models.Model):
    nit = models.CharField("NIT", max_length=20, unique=True, db_index=True)
    dv = models.CharField("Dígito de Verificación", max_length=2, blank=True)
    legal_name = models.CharField("Razón Social", max_length=255)
    ciiu = models.CharField("Código CIIU", max_length=10, blank=True)
    registration_date = models.DateField("Fecha de Registro", null=True, blank=True)
    status = models.CharField("Estado de Matrícula", max_length=50, default="ACTIVA")
    city = models.CharField("Ciudad / Municipio", max_length=100, blank=True)
    size = models.CharField(
        "Tamaño de Empresa",
        max_length=20,
        choices=CompanySize.choices,
        default=CompanySize.MICRO,
    )
    last_synced_at = models.DateTimeField("Última Sincronización", auto_now=True)
    created_at = models.DateTimeField("Fecha de Creación", auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de Empresa"
        verbose_name_plural = "Perfiles de Empresas"
        ordering = ["legal_name"]

    def __str__(self):
        return f"{self.nit} - {self.legal_name}"


class CompanyMembership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Usuario",
    )
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Empresa",
    )
    status = models.CharField(
        "Estado del Vínculo",
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.PENDING,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_memberships",
        verbose_name="Aprobado por",
    )
    created_at = models.DateTimeField("Solicitado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    class Meta:
        verbose_name = "Vínculo de Empresa"
        verbose_name_plural = "Vínculos de Empresas"
        unique_together = ("user", "company")

    def __str__(self):
        return f"{self.user.email} <-> {self.company.nit} ({self.get_status_display()})"
