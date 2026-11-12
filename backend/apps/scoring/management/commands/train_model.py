import os
from django.core.management.base import BaseCommand
from ml.src.train import train_and_export_model
from apps.scoring.models import ModelVersion


class Command(BaseCommand):
    help = "Entrena el modelo de scoring XGBoost, lo calibra y registra una versión activa en la BD."

    def handle(self, *args, **options):
        self.stdout.write("Iniciando entrenamiento y calibración del modelo XGBoost...")
        res = train_and_export_model()

        model_version, created = ModelVersion.objects.update_or_create(
            version=res["version"],
            defaults={
                "algorithm": "XGBoost + Calibración Sigmoide",
                "features": ["current_ratio", "debt_ratio", "net_margin", "roa", "interest_coverage", "log_assets", "company_age", "size_encoded"],
                "metrics": res["metrics"],
                "dataset_hash": res["metrics"].get("dataset_hash", ""),
                "artifact_path": res["artifact_path"],
                "is_active": True,
            },
        )

        action_str = "Creado y activado" if created else "Actualizado y activado"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action_str} modelo versión {model_version.version}.\n"
                f"AUC Test: {res['metrics']['auc_test']} | KS Test: {res['metrics']['ks_test']} | Brier: {res['metrics']['brier_test']}"
            )
        )
