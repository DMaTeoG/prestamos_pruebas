import pytest
from rest_framework.exceptions import ValidationError
from apps.accounts.models import CustomUser, Role
from apps.companies.models import CompanyProfile
from apps.scoring.services import (
    evaluate_company,
    get_active_model_version,
    validate_safe_artifact_path,
)
from apps.scoring.models import Evaluation, ModelVersion


# ==============================================================================
# Semana 1: Patrón AAA (Arrange, Act, Assert)
# Semana 2: Valores Límite (BVA) & Parametrización en Inferencia ML
# ==============================================================================


@pytest.mark.django_db
class TestScoringPipeline:
    def setup_method(self):
        # Arrange global de la clase de prueba
        self.analyst = CustomUser.objects.create_user(
            email="analyst@banco.com", password="pass", role=Role.ANALYST
        )
        self.company = CompanyProfile.objects.create(
            nit="800197268-4",
            legal_name="BANCOLOMBIA S.A. MOCK",
            ciiu="6412",
            registration_date="2015-03-10",
            size="GRANDE",
        )

    def test_active_model_version_creation_aaa(self):
        """Verifica la obtención y activación del modelo ML con AAA."""
        # Arrange: Entorno inicial

        # Act: Obtener la versión activa del modelo
        model_ver = get_active_model_version()

        # Assert: Aserción sobre el estado activo y unicidad
        assert model_ver is not None
        assert model_ver.is_active is True
        assert ModelVersion.objects.filter(is_active=True).count() == 1

    @pytest.mark.parametrize(
        "unsafe_path",
        [
            "C:/Windows/System32/evil.joblib",
            "/etc/passwd",
            "../../secret_credentials.joblib",
            "https://malicious-site.com/model.joblib",
        ],
    )
    def test_artifact_path_security_validation_parametrized_aaa(self, unsafe_path: str):
        """Verifica rechazo de rutas inseguras con @pytest.mark.parametrize y pytest.raises."""
        # Arrange: Ruta insegura
        path_under_test = unsafe_path

        # Act & Assert: Validación defensiva
        with pytest.raises(ValidationError):
            validate_safe_artifact_path(path_under_test)

    def test_company_scoring_evaluation_and_reproducibility_aaa(self):
        """Evalúa inferencia de scoring, límites BVA y reproducibilidad determinista con AAA."""
        # Arrange: Entidad y analista disponibles
        company = self.company
        analyst = self.analyst

        # Act: Ejecutar scoring dos veces sobre los mismos datos
        eval_1 = evaluate_company(company, analyst)
        eval_2 = evaluate_company(company, analyst)

        # Assert: Verificación de atributos e intervalos válidos (BVA)
        assert eval_1.pk is not None
        assert eval_1.company == company
        assert eval_1.requested_by == analyst
        # BVA: Score contenido estrictamente entre 0 y 1000
        assert 0 <= eval_1.score <= 1000
        # BVA: Probabilidad de Incumplimiento contenida estrictamente entre 0.0 y 1.0
        assert 0.0 <= eval_1.pd <= 1.0
        assert eval_1.risk_level in ["BAJO", "MEDIO", "ALTO", "MUY_ALTO"]
        assert 1 <= len(eval_1.factors) <= 5
        assert "pts." in eval_1.factors[0]["text"]
        assert "ratios" in eval_1.inputs_snapshot

        # Reproducibilidad: Evaluaciones idénticas producen exactamente el mismo score y PD
        assert eval_1.score == eval_2.score
        assert eval_1.pd == eval_2.pd
        assert Evaluation.objects.count() == 2

    def test_seed_demo_command_aaa(self):
        """Verifica la carga de datos sintéticos de demostración con AAA."""
        # Arrange
        from django.core.management import call_command

        # Act
        call_command("seed_demo")

        # Assert
        assert CustomUser.objects.filter(email="admin.demo@banco.com").exists()
        assert CustomUser.objects.filter(email="analista.demo@banco.com").exists()
        assert CustomUser.objects.filter(email="empresa.demo@empresa.com").exists()
        assert Evaluation.objects.filter(company__nit="800197268-4").exists()
