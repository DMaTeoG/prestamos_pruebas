from decimal import Decimal

import pytest

from apps.companies.models import CompanyProfile
from apps.financials.models import FinancialStatement
from apps.financials.ratios import calculate_financial_ratios, safe_divide

# ==============================================================================
# Semana 1: Patrón AAA
# Semana 2: BVA & Parametrización en Cálculos Financieros
# ==============================================================================


@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        (100, 20, 5.0),          # División estándar
        (100, 0, None),          # Límite crítico: Denominador cero
        (0, 100, 0.0),           # Límite: Numerador cero
        (None, 50, None),        # Entrada nula en numerador
        (50, None, None),        # Entrada nula en denominador
        (-100, 20, -5.0),        # Negativos
        (100, -20, -5.0),        # Denominador negativo
        (1, 3, 0.3333),          # Redondeo a 4 decimales
        (0.0001, 10000, 0.0),    # Valor infinitesimal
    ],
)
def test_safe_divide_bva_parametrized(numerator, denominator, expected):
    """Prueba unitaria parametrizada de división segura bajo el patrón AAA."""
    # Arrange: Preparar entradas
    num = numerator
    den = denominator

    # Act: Ejecutar la función matemática
    result = safe_divide(num, den)

    # Assert: Validar resultado esperado
    assert result == expected


@pytest.mark.django_db
class TestFinancialRatios:
    def setup_method(self):
        # Arrange global de la clase de prueba
        self.company = CompanyProfile.objects.create(
            nit="900123456-7",
            legal_name="EMPRESA DE PRUEBA S.A.S.",
            ciiu="6201",
        )

    def test_complete_ratios_calculation_aaa(self):
        """Cálculo integral de ratios estructurado estrictamente con AAA."""
        # Arrange: Construcción de estados financieros actual y previo
        stmt = FinancialStatement.objects.create(
            company=self.company,
            fiscal_year=2023,
            revenue=Decimal("1000000000.00"),
            expenses=Decimal("700000000.00"),
            operating_income=Decimal("300000000.00"),
            net_income=Decimal("200000000.00"),
            total_assets=Decimal("800000000.00"),
            current_assets=Decimal("400000000.00"),
            total_liabilities=Decimal("300000000.00"),
            current_liabilities=Decimal("200000000.00"),
            financial_debt=Decimal("100000000.00"),
            financial_expenses=Decimal("50000000.00"),
        )
        prev_stmt = FinancialStatement.objects.create(
            company=self.company,
            fiscal_year=2022,
            revenue=Decimal("800000000.00"),
        )

        # Act: Ejecución del motor de ratios financieros
        ratios = calculate_financial_ratios(stmt, prev_stmt)

        # Assert: Verificación de cada indicador financiero
        assert ratios["current_ratio"] == 2.0         # 400M / 200M
        assert ratios["debt_ratio"] == 0.375          # 300M / 800M
        assert ratios["net_margin"] == 0.2            # 200M / 1000M
        assert ratios["roa"] == 0.25                  # 200M / 800M
        assert ratios["interest_coverage"] == 6.0     # 300M / 50M
        assert ratios["revenue_growth"] == 0.25       # (1000M - 800M) / 800M
        assert ratios["confidence_level"] == "ALTA"
        assert ratios["missing_ratios_count"] == 0

    def test_zero_division_and_missing_ratios_confidence_aaa(self):
        """Prueba de frontera con balances en cero bajo el patrón AAA."""
        # Arrange: Estado financiero con valores en cero
        stmt = FinancialStatement.objects.create(
            company=self.company,
            fiscal_year=2023,
            revenue=Decimal("0.00"),
            total_assets=Decimal("0.00"),
            current_liabilities=Decimal("0.00"),
            financial_expenses=Decimal("0.00"),
        )

        # Act: Cálculo de ratios con valores frontera
        ratios = calculate_financial_ratios(stmt)

        # Assert: Verificación de degradación de confianza
        assert ratios["current_ratio"] is None
        assert ratios["debt_ratio"] is None
        assert ratios["confidence_level"] == "BAJA"
        assert ratios["missing_ratios_count"] >= 3
