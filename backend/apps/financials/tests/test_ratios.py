from decimal import Decimal
import pytest
from apps.companies.models import CompanyProfile
from apps.financials.models import FinancialStatement
from apps.financials.ratios import calculate_financial_ratios, safe_divide


@pytest.mark.django_db
class TestFinancialRatios:
    def setup_method(self):
        self.company = CompanyProfile.objects.create(
            nit="900123456-7",
            legal_name="EMPRESA DE PRUEBA S.A.S.",
            ciiu="6201",
        )

    def test_safe_divide_edge_cases(self):
        assert safe_divide(100, 20) == 5.0
        assert safe_divide(100, 0) is None
        assert safe_divide(None, 50) is None
        assert safe_divide(50, None) is None

    def test_complete_ratios_calculation(self):
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

        ratios = calculate_financial_ratios(stmt, prev_stmt)

        assert ratios["current_ratio"] == 2.0  # 400M / 200M
        assert ratios["debt_ratio"] == 0.375  # 300M / 800M
        assert ratios["net_margin"] == 0.2  # 200M / 1000M
        assert ratios["roa"] == 0.25  # 200M / 800M
        assert ratios["interest_coverage"] == 6.0  # 300M / 50M
        assert ratios["revenue_growth"] == 0.25  # (1000M - 800M) / 800M
        assert ratios["confidence_level"] == "ALTA"
        assert ratios["missing_ratios_count"] == 0

    def test_zero_division_and_missing_ratios_confidence(self):
        stmt = FinancialStatement.objects.create(
            company=self.company,
            fiscal_year=2023,
            revenue=Decimal("0.00"),
            total_assets=Decimal("0.00"),
            current_liabilities=Decimal("0.00"),
            financial_expenses=Decimal("0.00"),
        )
        ratios = calculate_financial_ratios(stmt)

        assert ratios["current_ratio"] is None
        assert ratios["debt_ratio"] is None
        assert ratios["confidence_level"] == "BAJA"
        assert ratios["missing_ratios_count"] >= 3
