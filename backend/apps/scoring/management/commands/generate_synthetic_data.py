import os
from django.core.management.base import BaseCommand
from ml.src.synth import generate_synthetic_dataset


class Command(BaseCommand):
    help = "Genera el dataset sintético de empresas colombianas con default a 12 meses."

    def add_arguments(self, parser):
        parser.add_argument("--companies", type=int, default=5000, help="Número de empresas a generar")
        parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")

    def handle(self, *args, **options):
        num_companies = options["companies"]
        seed = options["seed"]

        self.stdout.write(f"Generando dataset sintético para {num_companies} empresas (semilla: {seed})...")
        df = generate_synthetic_dataset(num_companies=num_companies, seed=seed)

        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../ml/data"))
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "synthetic_companies.csv")
        df.to_csv(out_path, index=False)

        self.stdout.write(self.style.SUCCESS(f"Dataset generado exitosamente en: {out_path} ({len(df)} registros)"))
