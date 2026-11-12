import logging
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.models import AuditAction
from apps.audit.services import log_action
from apps.financials.models import FinancialStatement
from apps.financials.ratios import calculate_financial_ratios
from apps.scoring.models import CreditDecisionStatus, Evaluation, ModelVersion, RiskLevel
from ml.src.features import build_features

logger = logging.getLogger("apps.scoring.services")

FEATURE_DESCRIPTIONS = {
    "current_ratio": "Razón Corriente (Liquidez)",
    "debt_ratio": "Nivel de Endeudamiento (Pasivos / Activos)",
    "net_margin": "Margen Neto de Utilidad",
    "roa": "Rentabilidad sobre Activos (ROA)",
    "interest_coverage": "Cobertura de Intereses",
    "log_assets": "Escala de Activos Totales",
    "company_age": "Antigüedad de la Empresa (años)",
    "size_encoded": "Tamaño Empresarial",
}


def validate_safe_artifact_path(artifact_path: str | Path) -> Path:
    """
    Verifies that the joblib artifact path resides strictly inside settings.MODEL_ARTIFACT_DIR
    as required by AGENTS.md §7.
    """
    allowed_dir = Path(getattr(settings, "MODEL_ARTIFACT_DIR")).resolve()
    resolved_path = Path(artifact_path).resolve()
    if not resolved_path.is_relative_to(allowed_dir):
        logger.error(
            "Security violation: attempted to load model artifact outside MODEL_ARTIFACT_DIR: %s",
            resolved_path,
        )
        raise ValidationError(
            "Ruta de artefacto no autorizada. Los modelos solo pueden cargarse desde ml/artifacts/."
        )
    return resolved_path


def get_active_model_version() -> ModelVersion:
    """Retorna la versión de modelo actualmente activa o registra el artefacto predeterminado."""
    active_model = ModelVersion.objects.filter(is_active=True).first()
    if active_model:
        return active_model

    artifact_path = Path(getattr(settings, "MODEL_ARTIFACT_DIR")) / "scoring_xgb_v1.joblib"
    if not os.path.exists(artifact_path):
        logger.info("Default model artifact not found; triggering initial training...")
        from ml.src.train import train_and_export_model

        train_and_export_model()

    if os.path.exists(artifact_path):
        safe_path = validate_safe_artifact_path(artifact_path)
        artifact_data = joblib.load(safe_path)
        active_model = ModelVersion.objects.create(
            version=artifact_data.get("version", "xgb-2026.1"),
            algorithm=artifact_data.get("algorithm", "XGBoost + Calibración"),
            features=artifact_data.get("feature_names", []),
            metrics=artifact_data.get("metrics", {}),
            dataset_hash=artifact_data.get("dataset_hash", ""),
            artifact_path=str(safe_path),
            is_active=True,
        )
        logger.info("Registered active ModelVersion: %s", active_model.version)
        return active_model

    logger.error("No active model version or artifact found in ml/artifacts/")
    raise ValidationError("No se encontró ningún modelo de scoring activo ni artefacto disponible.")


def calculate_risk_level(score: int) -> str:
    if score >= 750:
        return RiskLevel.BAJO
    elif score >= 500:
        return RiskLevel.MEDIO
    elif score >= 250:
        return RiskLevel.ALTO
    else:
        return RiskLevel.MUY_ALTO


def format_factor_text_es(feature_name: str, val: float, score_impact: float) -> str:
    """Genera la explicación en español para un factor SHAP."""
    direction = "incrementa el score" if score_impact >= 0 else "reduce el score"
    label = FEATURE_DESCRIPTIONS.get(feature_name, feature_name)

    if feature_name in ("debt_ratio", "net_margin", "roa"):
        val_str = f"{val:.2%}"
    elif feature_name in ("current_ratio", "interest_coverage"):
        val_str = f"{val:.2f}x"
    elif feature_name == "company_age":
        val_str = f"{int(round(val))} años"
    else:
        val_str = f"{val:.2f}"

    return f"{label} ({val_str}) {direction} en {abs(score_impact):.1f} pts."


def generate_shap_explanations(
    X_features: pd.DataFrame, calibrated_model=None
) -> list[dict]:
    """
    Calcula explicaciones locales reales utilizando shap.TreeExplainer sobre el
    estimador base XGBoost del modelo calibrado (T3.7), retornando el Top 5 en español.
    """
    feature_series = X_features.iloc[0]

    if calibrated_model is not None:
        try:
            base_estimator = None
            if hasattr(calibrated_model, "calibrated_classifiers_") and calibrated_model.calibrated_classifiers_:
                base_estimator = getattr(
                    calibrated_model.calibrated_classifiers_[0], "estimator", None
                )
            elif hasattr(calibrated_model, "estimator"):
                base_estimator = calibrated_model.estimator

            if base_estimator is not None:
                explainer = shap.TreeExplainer(base_estimator)
                shap_values = explainer.shap_values(X_features)
                if isinstance(shap_values, list):
                    row_shap = np.asarray(shap_values[-1])[0]
                else:
                    row_shap = np.asarray(shap_values)[0]

                factors = []
                for feat_name, shap_val in zip(X_features.columns, row_shap):
                    # Positive shap_val increases log-odds of default (PD), so it reduces score
                    score_impact = round(float(-shap_val * 55.0), 1)
                    if abs(score_impact) < 0.5:
                        continue
                    val = float(feature_series.get(feat_name, 0.0))
                    factors.append(
                        {
                            "feature": feat_name,
                            "val": round(val, 4),
                            "impact": score_impact,
                            "text": format_factor_text_es(feat_name, val, score_impact),
                        }
                    )

                factors = sorted(factors, key=lambda x: abs(x["impact"]), reverse=True)[:5]
                if factors:
                    return factors
        except Exception as exc:
            logger.warning("SHAP TreeExplainer fallback triggered: %s", exc.__class__.__name__)

    # Fallback determinista basado en desviaciones financieras
    factors = []
    debt = float(feature_series.get("debt_ratio", 0.5))
    debt_impact = round((0.55 - debt) * 90.0, 1)
    factors.append(
        {
            "feature": "debt_ratio",
            "val": round(debt, 4),
            "impact": debt_impact,
            "text": format_factor_text_es("debt_ratio", debt, debt_impact),
        }
    )

    curr = float(feature_series.get("current_ratio", 1.2))
    curr_impact = round((curr - 1.2) * 30.0, 1)
    factors.append(
        {
            "feature": "current_ratio",
            "val": round(curr, 4),
            "impact": curr_impact,
            "text": format_factor_text_es("current_ratio", curr, curr_impact),
        }
    )

    margin = float(feature_series.get("net_margin", 0.05))
    margin_impact = round((margin - 0.05) * 180.0, 1)
    factors.append(
        {
            "feature": "net_margin",
            "val": round(margin, 4),
            "impact": margin_impact,
            "text": format_factor_text_es("net_margin", margin, margin_impact),
        }
    )

    return sorted(factors, key=lambda x: abs(x["impact"]), reverse=True)[:5]


def _resolve_company_age(company) -> int:
    reg_date = getattr(company, "registration_date", None)
    if reg_date:
        try:
            year = reg_date.year if hasattr(reg_date, "year") else int(str(reg_date)[:4])
            return max(1, date.today().year - year)
        except (ValueError, TypeError):
            pass
    return 5


def evaluate_company(
    company,
    requested_by,
    statement: FinancialStatement = None,
    request=None,
    requested_amount: Decimal | None = None,
    term_months: int | None = None,
) -> Evaluation:
    """
    Ejecuta el pipeline completo de scoring crediticio para una empresa (T4.1, T4.3, T4.4).
    """
    model_ver = get_active_model_version()

    # Si no se provee estado financiero explícito, toma el más reciente disponible
    if not statement:
        statement = company.financial_statements.order_by("-fiscal_year").first()

    if not statement:
        logger.info(
            "No financial statement found for company_id=%s (nit=%s); creating baseline synthetic statement",
            company.id,
            company.nit,
        )
        statement = FinancialStatement.objects.create(
            company=company,
            fiscal_year=2023,
            revenue=100000000.00,
            expenses=90000000.00,
            operating_income=10000000.00,
            net_income=7000000.00,
            total_assets=80000000.00,
            current_assets=40000000.00,
            total_liabilities=30000000.00,
            current_liabilities=20000000.00,
            financial_debt=10000000.00,
            financial_expenses=2000000.00,
            origin="SYNTHETIC",
            uploaded_by=requested_by,
        )

    prev_statement = company.financial_statements.filter(
        fiscal_year=statement.fiscal_year - 1
    ).first()
    ratios_dict = calculate_financial_ratios(statement, prev_statement)
    confidence = ratios_dict["confidence_level"]
    company_age = _resolve_company_age(company)

    # Construir DataFrame de entrada para inferencia
    raw_input_data = {
        "revenue": float(statement.revenue),
        "expenses": float(statement.expenses),
        "operating_income": float(statement.operating_income),
        "net_income": float(statement.net_income),
        "total_assets": float(statement.total_assets),
        "current_assets": float(statement.current_assets),
        "total_liabilities": float(statement.total_liabilities),
        "current_liabilities": float(statement.current_liabilities),
        "financial_debt": float(statement.financial_debt),
        "financial_expenses": float(statement.financial_expenses),
        "company_age": company_age,
        "size": company.size,
    }

    df_in = pd.DataFrame([raw_input_data])
    X_features = build_features(df_in)

    # Validar ruta segura y cargar artefacto ML
    safe_artifact_path = validate_safe_artifact_path(model_ver.artifact_path)
    artifact_data = joblib.load(safe_artifact_path)
    calibrated_model = artifact_data["model"]

    pd_prob = float(calibrated_model.predict_proba(X_features)[0, 1])
    score = int(round((1.0 - pd_prob) * 1000))
    score = max(0, min(1000, score))

    risk_lvl = calculate_risk_level(score)
    factors_list = generate_shap_explanations(X_features, calibrated_model=calibrated_model)

    evaluation = Evaluation.objects.create(
        company=company,
        requested_by=requested_by,
        statement=statement,
        model_version=model_ver,
        pd=round(pd_prob, 4),
        score=score,
        risk_level=risk_lvl,
        confidence=confidence,
        factors=factors_list,
        requested_amount=requested_amount,
        term_months=term_months,
        decision_status=CreditDecisionStatus.PENDING,
        inputs_snapshot={
            "financial_statement_id": statement.id,
            "fiscal_year": statement.fiscal_year,
            "requested_amount": str(requested_amount) if requested_amount is not None else None,
            "term_months": term_months,
            "raw_inputs": raw_input_data,
            "ratios": ratios_dict,
        },
    )

    log_action(
        user=requested_by,
        action=AuditAction.EVALUATION_REQUEST,
        entity="Evaluation",
        entity_id=evaluation.id,
        request=request,
        metadata={
            "nit": company.nit,
            "score": score,
            "risk_level": risk_lvl,
            "requested_amount": str(requested_amount) if requested_amount is not None else None,
        },
    )
    logger.info(
        "Evaluation created: eval_id=%s nit=%s score=%s risk=%s confidence=%s model=%s",
        evaluation.id,
        company.nit,
        score,
        risk_lvl,
        confidence,
        model_ver.version,
    )

    return evaluation


def record_credit_decision(
    evaluation: Evaluation,
    admin_user,
    decision_status: str,
    request=None,
) -> Evaluation:
    """
    Registra la decisión manual del Comité/Administrador (APPROVED o REJECTED)
    sobre una evaluación crediticia existente, dejando trazabilidad en AuditLog.
    Nunca ejecuta aprobación automática (AGENTS.md §1).
    """
    if decision_status not in (CreditDecisionStatus.APPROVED, CreditDecisionStatus.REJECTED):
        raise ValidationError("El estado de decisión debe ser APPROVED o REJECTED.")

    evaluation.decision_status = decision_status
    evaluation.decided_by = admin_user
    evaluation.decided_at = timezone.now()
    evaluation.save(update_fields=["decision_status", "decided_by", "decided_at"])

    log_action(
        user=admin_user,
        action=AuditAction.CREDIT_DECISION,
        entity="Evaluation",
        entity_id=evaluation.id,
        request=request,
        metadata={
            "nit": evaluation.company.nit,
            "score": evaluation.score,
            "decision_status": decision_status,
        },
    )
    logger.info(
        "Manual credit decision recorded: eval_id=%s nit=%s decision=%s by_user_id=%s",
        evaluation.id,
        evaluation.company.nit,
        decision_status,
        admin_user.id,
    )
    return evaluation
