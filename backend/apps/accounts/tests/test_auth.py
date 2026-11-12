import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Role
from apps.companies.models import CompanyMembership, CompanyProfile

# ==============================================================================
# Semana 1: Patrón AAA (Arrange, Act, Assert) en Autenticación y Autorización
# ==============================================================================


@pytest.mark.django_db
class TestAuthSystem:
    def setup_method(self):
        # Arrange general para la suite de pruebas
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

    def test_user_creation_and_roles_aaa(self):
        """Verifica la persistencia y hashing de contraseñas bajo el patrón AAA."""
        # Arrange: Datos precargados en setup_method
        target_user = self.user

        # Act: Lectura de atributos del modelo
        email = target_user.email
        role = target_user.role
        password_valid = target_user.check_password("Password123!")

        # Assert: Aserciones explícitas
        assert email == "analista@banco.com"
        assert role == Role.ANALYST
        assert password_valid is True

    def test_login_success_and_cookie_jwt_auth_aaa(self):
        """Autenticación exitosa y generación de JWT en cookie httpOnly con AAA."""
        # Arrange
        url = reverse("auth-login")
        login_credentials = {"email": "analista@banco.com", "password": "Password123!"}

        # Act
        response = self.client.post(url, login_credentials, format="json")

        # Assert
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "analista@banco.com"
        assert response.data["user"]["role"] == Role.ANALYST
        assert "access_token" in response.cookies

        # Act 2: Consumo de /me usando la cookie generada
        url_me = reverse("auth-me")
        res_cookie = self.client.get(url_me)

        # Assert 2
        assert res_cookie.status_code == 200
        assert res_cookie.data["email"] == "analista@banco.com"

    def test_login_invalid_credentials_aaa(self):
        """Rechazo de credenciales inválidas retornando HTTP 401 con AAA."""
        # Arrange
        url = reverse("auth-login")
        wrong_credentials = {"email": "analista@banco.com", "password": "WrongPassword"}

        # Act
        response = self.client.post(url, wrong_credentials, format="json")

        # Assert
        assert response.status_code == 401
        assert "code" in response.data

    def test_profile_authenticated_and_logout_aaa(self):
        """Flujo de autenticación con Bearer token y posterior logout con AAA."""
        # Arrange: Login y obtención del JWT
        url_login = reverse("auth-login")
        login_res = self.client.post(
            url_login,
            {"email": "analista@banco.com", "password": "Password123!"},
            format="json",
        )
        token = login_res.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Act
        res_me = self.client.get(reverse("auth-me"))
        res_logout = self.client.post(reverse("auth-logout"))

        # Assert
        assert res_me.status_code == 200
        assert res_me.data["email"] == "analista@banco.com"
        assert res_logout.status_code == 200

    def test_admin_endpoints_role_matrix_aaa(self):
        """Matriz de control de acceso basada en roles (RBAC) con AAA."""
        # Arrange: Creación de empresa y membresía pendiente
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

        # Act & Assert 1: Rol Analista denegado en endpoints de administración
        self.client.force_authenticate(user=self.user)
        assert self.client.get(reverse("admin-user-list")).status_code == 403
        assert self.client.get(reverse("admin-membership-list")).status_code == 403

        # Act & Assert 2: Rol Empresa denegado en endpoints de administración
        self.client.force_authenticate(user=self.company_user)
        assert self.client.get(reverse("admin-user-list")).status_code == 403
        assert self.client.patch(
            reverse("admin-membership-update", kwargs={"pk": membership.id}),
            {"status": "APPROVED"},
            format="json",
        ).status_code == 403

        # Act & Assert 3: Rol Administrador con acceso completo y capacidad de aprobación
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
