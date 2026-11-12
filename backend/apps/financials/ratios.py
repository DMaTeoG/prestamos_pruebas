from decimal import Decimal
from typing import Dict, Any


def safe_divide(numerator: Decimal | float | int, denominator: Decimal | float | int) -> float | None:
    """Realiza una división segura retornando None si el denominador es 0 o nulo."""
    if numerator is None or denominator is None:
        return None
    try:
        num = float(numerator)
        den = float(denominator)
        if den == 0.0:
            return None
        return round(num / den, 4)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def calculate_financial_ratios(statement, previous_statement=None) -> Dict[str, Any]:
    """
    Calcula los 5 ratios financieros principales + crecimiento interanual de ingresos
    a partir de una instancia de FinancialStatement.
    Maneja divisiones por cero y determina el nivel de confianza de completitud.
    """
    missing_count = 0

    # 1. Liquidez Corriente (Razón Corriente)
    current_ratio = safe_divide(statement.current_assets, statement.current_liabilities)
    if current_ratio is None:
        missing_count += 1

    # 2. Nivel de Endeudamiento (Pasivos / Activos)
    debt_ratio = safe_divide(statement.total_liabilities, statement.total_assets)
    if debt_ratio is None:
        missing_count += 1

    # 3. Margen Neto (Utilidad Neta / Ingresos)
    net_margin = safe_divide(statement.net_income, statement.revenue)
    if net_margin is None:
        missing_count += 1

    # 4. ROA - Rentabilidad sobre Activos (Utilidad Neta / Activos Totales)
    roa = safe_divide(statement.net_income, statement.total_assets)
    if roa is None:
        missing_count += 1

    # 5. Cobertura de Intereses (EBIT / Gastos Financieros)
    interest_coverage = safe_divide(statement.operating_income, statement.financial_expenses)
    if interest_coverage is None:
        missing_count += 1

    # 6. Crecimiento de Ingresos (interanual)
    revenue_growth = None
    if previous_statement and previous_statement.revenue:
        prev_rev = float(previous_statement.revenue)
        curr_rev = float(statement.revenue)
        if prev_rev > 0:
            revenue_growth = round((curr_rev - prev_rev) / prev_rev, 4)

    # Determinación de Nivel de Confianza (T2.6)
    if missing_count == 0:
        confidence_level = "ALTA"
    elif missing_count <= 2:
        confidence_level = "MEDIA"
    else:
        confidence_level = "BAJA"

    return {
        "current_ratio": current_ratio,
        "debt_ratio": debt_ratio,
        "net_margin": net_margin,
        "roa": roa,
        "interest_coverage": interest_coverage,
        "revenue_growth": revenue_growth,
        "confidence_level": confidence_level,
        "missing_ratios_count": missing_count,
    }
