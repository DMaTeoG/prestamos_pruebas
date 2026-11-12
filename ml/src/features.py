import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "current_ratio",
    "debt_ratio",
    "net_margin",
    "roa",
    "interest_coverage",
    "log_assets",
    "company_age",
    "size_encoded",
]

SIZE_MAP = {
    "MICRO": 1,
    "PEQUENA": 2,
    "MEDIANA": 3,
    "GRANDE": 4,
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fuente única de verdad para el cálculo e imputación de características (features).
    Se utiliza idénticamente durante el entrenamiento offline y la inferencia online en Django.
    """
    X = pd.DataFrame(index=df.index)

    # Convert numeric columns safely
    curr_assets = pd.to_numeric(df.get("current_assets", 0), errors="coerce").fillna(0)
    curr_liab = pd.to_numeric(df.get("current_liabilities", 0), errors="coerce").fillna(0)
    tot_assets = pd.to_numeric(df.get("total_assets", 0), errors="coerce").fillna(0)
    tot_liab = pd.to_numeric(df.get("total_liabilities", 0), errors="coerce").fillna(0)
    net_inc = pd.to_numeric(df.get("net_income", 0), errors="coerce").fillna(0)
    rev = pd.to_numeric(df.get("revenue", 0), errors="coerce").fillna(0)
    op_inc = pd.to_numeric(df.get("operating_income", 0), errors="coerce").fillna(0)
    fin_exp = pd.to_numeric(df.get("financial_expenses", 0), errors="coerce").fillna(0)

    # 1. Razón Corriente (Imputación mediana por defecto = 1.2)
    X["current_ratio"] = np.where(curr_liab > 0, curr_assets / curr_liab, 1.2)
    X["current_ratio"] = X["current_ratio"].clip(0, 20)

    # 2. Endeudamiento (Imputación mediana por defecto = 0.5)
    X["debt_ratio"] = np.where(tot_assets > 0, tot_liab / tot_assets, 0.5)
    X["debt_ratio"] = X["debt_ratio"].clip(0, 5)

    # 3. Margen Neto (Imputación mediana por defecto = 0.05)
    X["net_margin"] = np.where(rev > 0, net_inc / rev, 0.05)
    X["net_margin"] = X["net_margin"].clip(-2, 2)

    # 4. ROA (Imputación mediana por defecto = 0.04)
    X["roa"] = np.where(tot_assets > 0, net_inc / tot_assets, 0.04)
    X["roa"] = X["roa"].clip(-2, 2)

    # 5. Cobertura de Intereses (Imputación por defecto = 3.0)
    X["interest_coverage"] = np.where(fin_exp > 0, op_inc / fin_exp, 3.0)
    X["interest_coverage"] = X["interest_coverage"].clip(-10, 50)

    # 6. Logaritmo de Activos Totales
    X["log_assets"] = np.log1p(np.maximum(0, tot_assets))

    # 7. Antigüedad de la Empresa
    X["company_age"] = pd.to_numeric(df.get("company_age", 5), errors="coerce").fillna(5).clip(1, 100)

    # 8. Tamaño Codificado
    sizes = df.get("size", "MICRO")
    if isinstance(sizes, str):
        X["size_encoded"] = SIZE_MAP.get(sizes, 1)
    else:
        X["size_encoded"] = sizes.map(lambda s: SIZE_MAP.get(str(s).upper(), 1)).fillna(1)

    return X[FEATURE_COLUMNS]
