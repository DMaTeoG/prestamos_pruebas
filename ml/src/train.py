import os
import hashlib
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss

from ml.src.synth import generate_synthetic_dataset
from ml.src.features import build_features, FEATURE_COLUMNS


def calculate_ks_statistic(y_true, y_prob):
    """Calcula la estadística Kolmogorov-Smirnov (KS)."""
    df_eval = pd.DataFrame({"target": y_true, "prob": y_prob})
    df_eval = df_eval.sort_values("prob", ascending=False)
    
    total_events = (df_eval["target"] == 1).sum()
    total_nonevents = (df_eval["target"] == 0).sum()
    
    if total_events == 0 or total_nonevents == 0:
        return 0.0

    df_eval["cum_events"] = (df_eval["target"] == 1).cumsum() / total_events
    df_eval["cum_nonevents"] = (df_eval["target"] == 0).cumsum() / total_nonevents
    
    ks = np.abs(df_eval["cum_events"] - df_eval["cum_nonevents"]).max()
    return round(float(ks), 4)


def train_and_export_model(out_dir: str = None) -> dict:
    """
    Entrena, evalúa, calibra y exporta el modelo de scoring crediticio.
    Aplica partición temporal estricta por año fiscal (anti-leakage).
    """
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(__file__), "../artifacts")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Generar / Cargar Dataset Sintético
    df_raw = generate_synthetic_dataset(num_companies=5000, seed=42)
    dataset_bytes = df_raw.to_csv(index=False).encode("utf-8")
    dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()[:16]

    # 2. Extraer Features (Única fuente de verdad)
    X = build_features(df_raw)
    y = df_raw["default_12m"]
    years = df_raw["fiscal_year"]

    # 3. Partición Temporal Estricta
    train_mask = years.isin([2020, 2021])
    val_mask = (years == 2022)
    test_mask = (years == 2023)

    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    # 4. Entrenar Baseline (Regresión Logística)
    baseline = LogisticRegression(max_iter=1000, random_state=42)
    baseline.fit(X_train, y_train)
    p_val_base = baseline.predict_proba(X_val)[:, 1]
    auc_base = roc_auc_score(y_val, p_val_base)

    # 5. Entrenar XGBoost Classifier
    xgb_base = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
    )
    
    # 6. Calibración de Probabilidades con CalibratedClassifierCV
    calibrated_model = CalibratedClassifierCV(estimator=xgb_base, method="sigmoid", cv=3)
    calibrated_model.fit(X_train, y_train)

    # 7. Evaluación en Test Set (2023)
    p_test = calibrated_model.predict_proba(X_test)[:, 1]
    auc_test = float(roc_auc_score(y_test, p_test))
    ks_test = float(calculate_ks_statistic(y_test, p_test))
    brier_test = float(brier_score_loss(y_test, p_test))

    metrics = {
        "auc_baseline": round(float(auc_base), 4),
        "auc_test": round(auc_test, 4),
        "ks_test": round(ks_test, 4),
        "brier_test": round(brier_test, 4),
        "test_sample_size": int(len(y_test)),
        "dataset_hash": dataset_hash,
    }

    # 8. Guardar Artefacto Serializado (.joblib)
    artifact_data = {
        "version": "xgb-2026.1",
        "algorithm": "XGBoost + Sigmoid Calibration",
        "feature_names": FEATURE_COLUMNS,
        "model": calibrated_model,
        "metrics": metrics,
        "dataset_hash": dataset_hash,
    }

    artifact_filename = "scoring_xgb_v1.joblib"
    artifact_path = os.path.join(out_dir, artifact_filename)
    joblib.dump(artifact_data, artifact_path)

    return {
        "artifact_path": artifact_path,
        "version": "xgb-2026.1",
        "metrics": metrics,
    }


if __name__ == "__main__":
    res = train_and_export_model()
    print("Model Training & Export Complete!")
    print(f"Artifact Path: {res['artifact_path']}")
    print(f"Metrics: {res['metrics']}")
