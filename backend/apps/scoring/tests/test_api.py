import io

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Role
from apps.companies.models import CompanyMembership, CompanyProfile


@pytest.mark.django_db
class TestScoringAPI:
    def setup_method(self):
        self.client = APIClient()
        self.analyst = CustomUser.objects.create_user(
            email="analyst_api@banco.com", password="Password123!", role=Role.ANALYST
        )
        self.admin_user = CustomUser.objects.create_user(
            email="admin_api@banco.com", password="Password123!", role=Role.ADMIN
        )
        self.company_user = CustomUser.objects.create_user(
            email="company_api@banco.com", password="Password123!", role=Role.COMPANY
        )
        self.company = CompanyProfile.objects.create(
            nit="800197268-4",
            legal_name="BANCOLOMBIA S.A.",
            ciiu="6412",
        )
        self.other_company = CompanyProfile.objects.create(
            nit="900123456-8",
            legal_name="OTRA EMPRESA S.A.S.",
            ciiu="4690",
        )

    def test_evaluations_post_as_analyst(self):
        self.client.force_authenticate(user=self.analyst)
        url = reverse("evaluation-list-create")
        res = self.client.post(url, {"nit": "800197268-4"}, format="json")

        assert res.status_code == 201
        assert "score" in res.data
        assert 0 <= res.data["score"] <= 1000
        assert "disclaimer" in res.data
        assert "El score es una estimación de riesgo" in res.data["disclaimer"]

    def test_evaluations_post_as_company_user_forbidden(self):
        self.client.force_authenticate(user=self.company_user)
        url = reverse("evaluation-list-create")
        res = self.client.post(url, {"nit": "800197268-4"}, format="json")

        assert res.status_code == 403
        assert res.data["code"] == "FORBIDDEN"

    def test_company_credit_request_and_admin_manual_decision(self):
        # 1. Approve membership for company_user on self.company
        CompanyMembership.objects.create(
            user=self.company_user,
            company=self.company,
            status="APPROVED",
        )

        # 2. Company submits credit study request with amount and term -> triggers ML scoring
        self.client.force_authenticate(user=self.company_user)
        url = reverse("evaluation-list-create")
        res = self.client.post(
            url,
            {
                "nit": "800197268-4",
                "requested_amount": "350000000.00",
                "term_months": 36,
            },
            format="json",
        )
        assert res.status_code == 201
        eval_id = res.data["id"]
        assert res.data["decision_status"] == "PENDING"
        assert res.data["requested_amount"] == "350000000.00"
        assert res.data["term_months"] == 36
        assert 0 <= res.data["score"] <= 1000

        # 3. Company or Analyst cannot call admin decision endpoint
        decision_url = reverse("admin-evaluation-decision", kwargs={"pk": eval_id})
        assert (
            self.client.patch(decision_url, {"decision_status": "APPROVED"}, format="json").status_code
            == 403
        )
        self.client.force_authenticate(user=self.analyst)
        assert (
            self.client.patch(decision_url, {"decision_status": "APPROVED"}, format="json").status_code
            == 403
        )

        # 4. Admin reviews score and registers manual decision (APPROVED)
        self.client.force_authenticate(user=self.admin_user)
        decision_res = self.client.patch(
            decision_url,
            {"decision_status": "APPROVED"},
            format="json",
        )
        assert decision_res.status_code == 200
        assert decision_res.data["decision_status"] == "APPROVED"
        assert decision_res.data["decided_by_email"] == "admin_api@banco.com"
        assert decision_res.data["decided_at"] is not None

    def test_evaluations_invalid_nit(self):
        self.client.force_authenticate(user=self.analyst)
        url = reverse("evaluation-list-create")
        res = self.client.post(url, {"nit": "INVALID_NIT_123"}, format="json")

        assert res.status_code == 400
        assert res.data["code"] == "INVALID_NIT"

    def test_company_lookup_api(self):
        self.client.force_authenticate(user=self.analyst)
        url = reverse("company-lookup") + "?nit=800197268-4"
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.data["nit"] == "800197268-4"
        assert res.data["legal_name"] == "BANCOLOMBIA S.A."

    def test_company_object_level_permissions_and_financial_upload(self):
        # Without approved membership, company_user is forbidden from accessing company detail & financials
        self.client.force_authenticate(user=self.company_user)
        detail_url = reverse("company-detail", kwargs={"pk": self.company.id})
        fin_url = reverse("financial-statement-list-create", kwargs={"company_id": self.company.id})
        csv_url = reverse("financial-statement-csv-import", kwargs={"company_id": self.company.id})

        assert self.client.get(detail_url).status_code == 403
        assert self.client.get(fin_url).status_code == 403

        # Approve membership for self.company
        CompanyMembership.objects.create(
            user=self.company_user,
            company=self.company,
            status="APPROVED",
        )

        # Now company_user can access its own company and upload statements
        assert self.client.get(detail_url).status_code == 200
        my_comp_res = self.client.get(reverse("company-my-company"))
        assert my_comp_res.status_code == 200
        assert my_comp_res.data["nit"] == "800197268-4"

        post_fin = self.client.post(
            fin_url,
            {
                "fiscal_year": 2023,
                "revenue": "1500000000.00",
                "expenses": "1100000000.00",
                "operating_income": "400000000.00",
                "net_income": "280000000.00",
                "total_assets": "2000000000.00",
                "current_assets": "800000000.00",
                "total_liabilities": "700000000.00",
                "current_liabilities": "350000000.00",
                "financial_debt": "250000000.00",
                "financial_expenses": "45000000.00",
            },
            format="json",
        )
        assert post_fin.status_code == 201
        assert post_fin.data["ratios"]["confidence_level"] == "ALTA"

        # CSV import on own company succeeds
        csv_content = (
            "fiscal_year,revenue,expenses,operating_income,net_income,"
            "total_assets,current_assets,total_liabilities,current_liabilities,"
            "financial_debt,financial_expenses\n"
            "2022,1200000000,900000000,300000000,200000000,1800000000,700000000,650000000,300000000,200000000,40000000\n"
        )
        csv_file = io.BytesIO(csv_content.encode("utf-8"))
        csv_file.name = "estados.csv"
        csv_res = self.client.post(csv_url, {"file": csv_file}, format="multipart")
        assert csv_res.status_code == 201

        # Still forbidden from accessing other_company
        other_detail_url = reverse("company-detail", kwargs={"pk": self.other_company.id})
        assert self.client.get(other_detail_url).status_code == 403
