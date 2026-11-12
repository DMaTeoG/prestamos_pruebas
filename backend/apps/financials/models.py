from django.db import models
from django.conf import settings
from apps.companies.models import CompanyProfile


class StatementOrigin(models.TextChoices):
    COMPANY = "COMPANY", "Cargado por Empresa"
    PUBLIC = "PUBLIC", "Fuente Pública"
    SYNTHETIC = "SYNTHETIC", "Sintético / Demo"


class FinancialStatement(models.Model):
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="financial_statements",
        verbose_name="Empresa",
    )
    fiscal_year = models.IntegerField("Año Fiscal")
    revenue = models.DecimalField("Ingresos Operacionales", max_digits=18, decimal_places=2, default=0)
    expenses = models.DecimalField("Gastos Operacionales", max_digits=18, decimal_places=2, default=0)
    operating_income = models.DecimalField("Utilidad Operativa (EBIT)", max_digits=18, decimal_places=2, default=0)
    net_income = models.DecimalField("Utilidad Neta", max_digits=18, decimal_places=2, default=0)
    total_assets = models.DecimalField("Activos Totales", max_digits=18, decimal_places=2, default=0)
    current_assets = models.DecimalField("Activos Corrientes", max_digits=18, decimal_places=2, default=0)
    total_liabilities = models.DecimalField("Pasivos Totales", max_digits=18, decimal_places=2, default=0)
    current_liabilities = models.DecimalField("Pasivos Corrientes", max_digits=18, decimal_places=2, default=0)
    financial_debt = models.DecimalField("Deuda Financiera", max_digits=18, decimal_places=2, default=0)
    financial_expenses = models.DecimalField("Gastos Financieros / Intereses", max_digits=18, decimal_places=2, default=0)

    origin = models.CharField(
        "Origen del Dato",
        max_length=20,
        choices=StatementOrigin.choices,
        default=StatementOrigin.COMPANY,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_financial_statements",
        verbose_name="Cargado por",
    )
    created_at = models.DateTimeField("Fecha de Registro", auto_now_add=True)

    class Meta:
        verbose_name = "Estado Financiero"
        verbose_name_plural = "Estados Financieros"
        unique_together = ("company", "fiscal_year")
        ordering = ["-fiscal_year"]

    def __str__(self):
        return f"{self.company.nit} - Año {self.fiscal_year} (${self.revenue:,.2f})"
