import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import CustomUser, Role
from apps.companies.models import CompanyProfile, CompanyMembership


@pytest.mark.django_db
class TestAuthSystem:
    def setup_method(self):
        self.client = APIClient()
        self.user_data = {
            "email": "analista@banco.com",
            "password": "Password123!",
            "first_name": "Carlos",
            "last_name": "Analista",
            "role": Role.ANALYST,
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.admin_user = CustomUser.objects.create_user(
            email="admin@banco.com",
            password="Password123!",
            role=Role.ADMIN,
        )
        self.company_user = CustomUser.objects.create_user(
            email="empresa@empresa.com",
            password="Password123!",
            role=Role.COMPANY,
        )

    def test_user_creation_and_roles(self):
        assert self.user.email == "analista@banco.com"
        assert self.user.role == Role.ANALYST
        assert self.user.check_password("Password123!")

    def test_login_success_and_cookie_jwt_auth(self):
        url = reverse("auth-login")
        response = self.client.post(
            url,
            {"email": "analista@banco.com", "password": "Password123!"},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "analista@banco.com"
        assert response.data["user"]["role"] == Role.ANALYST
        assert "access_token" in response.cookies

        # Authenticate using ONLY the httpOnly cookie (no Authorization header)
        url_me = reverse("auth-me")
        res_cookie = self.client.get(url_me)
        assert res_cookie.status_code == 200
        assert res_cookie.data["email"] == "analista@banco.com"

    def test_login_invalid_credentials(self):
        url = reverse("auth-login")
        response = self.client.post(
            url,
            {"email": "analista@banco.com", "password": "WrongPassword"},
            format="json",
        )
        assert response.status_code == 401
        assert "code" in response.data

    def test_profile_authenticated_and_logout(self):
        url_login = reverse("auth-login")
        login_res = self.client.post(
            url_login,
            {"email": "analista@banco.com", "password": "Password123!"},
            format="json",
        )
        token = login_res.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url_me = reverse("auth-me")
        res = self.client.get(url_me)
        assert res.status_code == 200
        assert res.data["email"] == "analista@banco.com"

        res_logout = self.client.post(reverse("auth-logout"))
        assert res_logout.status_code == 200

    def test_admin_endpoints_role_matrix(self):
        company = CompanyProfile.objects.create(
            nit="900123456-8",
            dv="8",
            legal_name="EMPRESA PRUEBA S.A.S.",
        )
        membership = CompanyMembership.objects.create(
            user=self.company_user,
            company=company,
            status="PENDING",
        )

        # Analyst cannot access Admin endpoints
        self.client.force_authenticate(user=self.user)
        assert self.client.get(reverse("admin-user-list")).status_code == 403
        assert self.client.get(reverse("admin-membership-list")).status_code == 403
        assert self.client.get(reverse("admin-model-list")).status_code == 403
        assert self.client.get(reverse("admin-audit-list")).status_code == 403

        # Company cannot access Admin endpoints
        self.client.force_authenticate(user=self.company_user)
        assert self.client.get(reverse("admin-user-list")).status_code == 403
        assert self.client.patch(
            reverse("admin-membership-update", kwargs={"pk": membership.id}),
            {"status": "APPROVED"},
            format="json",
        ).status_code == 403

        # Admin can access all Admin endpoints and approve membership
        self.client.force_authenticate(user=self.admin_user)
        assert self.client.get(reverse("admin-user-list")).status_code == 200
        assert self.client.get(reverse("admin-membership-list")).status_code == 200
        models_res = self.client.get(reverse("admin-model-list"))
        assert models_res.status_code == 200
        assert len(models_res.data) >= 1

        model_id = models_res.data[0]["id"]
        activate_res = self.client.post(
            reverse("admin-model-activate", kwargs={"pk": model_id})
        )
        assert activate_res.status_code == 200
        assert activate_res.data["is_active"] is True

        approve_res = self.client.patch(
            reverse("admin-membership-update", kwargs={"pk": membership.id}),
            {"status": "APPROVED"},
            format="json",
        )
        assert approve_res.status_code == 200
        assert approve_res.data["status"] == "APPROVED"

        audit_res = self.client.get(reverse("admin-audit-list"))
        assert audit_res.status_code == 200
        assert len(audit_res.data) >= 2
