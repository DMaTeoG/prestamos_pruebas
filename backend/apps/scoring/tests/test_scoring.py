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


@pytest.mark.django_db
class TestScoringPipeline:
    def setup_method(self):
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

    def test_active_model_version_creation(self):
        model_ver = get_active_model_version()
        assert model_ver is not None
        assert model_ver.is_active is True
        assert ModelVersion.objects.filter(is_active=True).count() == 1

    def test_artifact_path_security_validation(self):
        with pytest.raises(ValidationError):
            validate_safe_artifact_path("C:/Windows/System32/evil.joblib")

    def test_company_scoring_evaluation_and_reproducibility(self):
        eval_1 = evaluate_company(self.company, self.analyst)
        eval_2 = evaluate_company(self.company, self.analyst)

        assert eval_1.pk is not None
        assert eval_1.company == self.company
        assert eval_1.requested_by == self.analyst
        assert 0 <= eval_1.score <= 1000
        assert 0.0 <= eval_1.pd <= 1.0
        assert eval_1.risk_level in ["BAJO", "MEDIO", "ALTO", "MUY_ALTO"]
        assert 1 <= len(eval_1.factors) <= 5
        assert "pts." in eval_1.factors[0]["text"]
        assert "ratios" in eval_1.inputs_snapshot
        # Reproducibility on identical inputs (AGENTS.md §7, §9)
        assert eval_1.score == eval_2.score
        assert eval_1.pd == eval_2.pd
        assert Evaluation.objects.count() == 2

    def test_seed_demo_command(self):
        from django.core.management import call_command

        call_command("seed_demo")
        assert CustomUser.objects.filter(email="admin.demo@banco.com").exists()
        assert CustomUser.objects.filter(email="analista.demo@banco.com").exists()
        assert CustomUser.objects.filter(email="empresa.demo@empresa.com").exists()
        assert Evaluation.objects.filter(company__nit="800197268-4").exists()
