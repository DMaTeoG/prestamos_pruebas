import os
import numpy as np
import pandas as pd

def generate_synthetic_dataset(num_companies: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Genera un dataset sintético de empresas colombianas con trayectorias multianuales (2019-2023).
    Define la variable objetivo `default_12m` mediante una función de riesgo latente + ruido.
    """
    np.random.seed(seed)
    records = []
    
    ciiu_codes = ["4690", "6201", "4110", "1010", "7020", "1511", "2811"]
    size_levels = ["MICRO", "PEQUENA", "MEDIANA", "GRANDE"]
    
    for i in range(1, num_companies + 1):
        nit_num = 900000000 + i
        nit = f"{nit_num}-7"
        ciiu = np.random.choice(ciiu_codes)
        size = np.random.choice(size_levels, p=[0.5, 0.3, 0.15, 0.05])
        
        # Base scale depending on size
        if size == "MICRO":
            base_rev = np.random.uniform(50e6, 500e6)
        elif size == "PEQUENA":
            base_rev = np.random.uniform(500e6, 3000e6)
        elif size == "MEDIANA":
            base_rev = np.random.uniform(3000e6, 15000e6)
        else:
            base_rev = np.random.uniform(15000e6, 100000e6)
            
        base_assets = base_rev * np.random.uniform(0.8, 1.5)
        initial_age = np.random.randint(1, 25)
        
        # Generate 4 fiscal years (2020-2023)
        for yr_idx, year in enumerate([2020, 2021, 2022, 2023]):
            growth = np.random.normal(0.05, 0.15)
            revenue = max(10e6, base_rev * ((1 + growth) ** yr_idx))
            total_assets = max(15e6, base_assets * ((1 + growth * 0.8) ** yr_idx))
            
            # Financial metrics
            debt_ratio_factor = np.random.beta(2, 5) if size in ["MEDIANA", "GRANDE"] else np.random.beta(3, 3)
            total_liabilities = total_assets * debt_ratio_factor
            current_assets = total_assets * np.random.uniform(0.3, 0.7)
            current_liabilities = total_liabilities * np.random.uniform(0.4, 0.8)
            
            margin = np.random.normal(0.08, 0.12)
            net_income = revenue * margin
            expenses = revenue - net_income
            operating_income = net_income * np.random.uniform(1.1, 1.5)
            
            financial_debt = total_liabilities * np.random.uniform(0.2, 0.6)
            financial_expenses = financial_debt * np.random.uniform(0.08, 0.18)
            
            # Latent risk score calculation
            # High debt, low liquidity, negative margin, and high interest expenses increase default risk
            ratio_debt = total_liabilities / total_assets
            ratio_curr = current_assets / max(1.0, current_liabilities)
            ratio_margin = net_income / revenue
            ratio_cov = operating_income / max(1.0, financial_expenses)
            
            logit = (
                3.5 * ratio_debt
                - 1.2 * ratio_curr
                - 4.0 * ratio_margin
                - 0.3 * min(ratio_cov, 10.0)
                - 0.05 * (initial_age + yr_idx)
                + np.random.normal(0, 0.5)  # Noise
            )
            prob_default = 1.0 / (1.0 + np.exp(-logit + 1.5))
            default_12m = int(np.random.rand() < prob_default)
            
            records.append({
                "nit": nit,
                "fiscal_year": year,
                "company_age": initial_age + yr_idx,
                "ciiu": ciiu,
                "size": size,
                "revenue": round(revenue, 2),
                "expenses": round(expenses, 2),
                "operating_income": round(operating_income, 2),
                "net_income": round(net_income, 2),
                "total_assets": round(total_assets, 2),
                "current_assets": round(current_assets, 2),
                "total_liabilities": round(total_liabilities, 2),
                "current_liabilities": round(current_liabilities, 2),
                "financial_debt": round(financial_debt, 2),
                "financial_expenses": round(financial_expenses, 2),
                "default_12m": default_12m,
            })
            
    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "../data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_companies.csv")
    df = generate_synthetic_dataset(num_companies=5000, seed=42)
    df.to_csv(out_path, index=False)
    print(f"Generated synthetic dataset with {len(df)} rows at {out_path}")
