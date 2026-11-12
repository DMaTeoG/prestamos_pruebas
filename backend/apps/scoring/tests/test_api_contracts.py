"""Pruebas de Contrato de API (Semana 5) con `requests` y `jsonschema`.

Valida códigos de estado HTTP (200, 400, 404, etc.) y la estructura estricta
de los payloads JSON devueltos por los endpoints de la API.
"""

import json
import pytest
import requests
import jsonschema
from django.urls import reverse
from apps.accounts.models import CustomUser, Role
from apps.companies.models import CompanyProfile


# ------------------------------------------------------------------------------
# Definición de Esquemas JSON (Data Contracts)
# ------------------------------------------------------------------------------

HEALTH_CONTRACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["status", "database", "version"],
    "properties": {
        "status": {"type": "string", "enum": ["ok", "degraded"]},
        "database": {"type": "string", "enum": ["up", "down"]},
        "version": {"type": "string"},
    },
    "additionalProperties": False,
}

LOGIN_SUCCESS_CONTRACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["access", "refresh", "user"],
    "properties": {
        "access": {"type": "string", "minLength": 10},
        "refresh": {"type": "string", "minLength": 10},
        "user": {
            "type": "object",
            "required": ["id", "email", "role"],
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string"},
                "role": {"type": "string", "enum": ["ADMIN", "ANALYST", "COMPANY"]},
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": True,
}

ERROR_CONTRACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {"type": "string"},
        "code": {"type": "string"},
    },
    "additionalProperties": True,
}

COMPANY_LOOKUP_CONTRACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["nit", "legal_name", "ciiu"],
    "properties": {
        "nit": {"type": "string"},
        "legal_name": {"type": "string"},
        "ciiu": {"type": "string"},
        "origin": {"type": "string"},
    },
    "additionalProperties": True,
}


@pytest.mark.django_db
class TestApiJsonSchemaContracts:
    """Suite de validación de contratos JSON Schema usando la librería requests."""

    def test_health_check_endpoint_contract_with_requests(self, live_server):
        """Valida que GET /api/v1/health/ retorne HTTP 200 y cumpla con HEALTH_CONTRACT_SCHEMA."""
        # Arrange
        url = f"{live_server.url}/api/v1/health/"

        # Act: Ejecución real con la librería requests
        response = requests.get(url, timeout=5)

        # Assert: Código de estado HTTP 200 y validación de contrato con jsonschema
        assert response.status_code == 200
        payload = response.json()
        jsonschema.validate(instance=payload, schema=HEALTH_CONTRACT_SCHEMA)
        assert payload["status"] == "ok"
        assert payload["database"] == "up"

    def test_auth_login_contract_with_requests(self, live_server):
        """Valida autenticación vía POST /api/v1/auth/login/ y su contrato de respuesta."""
        # Arrange: Crear usuario de prueba
        user_email = "analyst_contract@banco.com"
        user_pass = "Password123!"
        CustomUser.objects.create_user(
            email=user_email,
            password=user_pass,
            role=Role.ANALYST,
        )
        url = f"{live_server.url}/api/v1/auth/login/"
        payload_data = {"email": user_email, "password": user_pass}

        # Act: Solicitud HTTP POST usando requests
        response = requests.post(
            url,
            data=json.dumps(payload_data),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        # Assert: HTTP 200 y conformidad con JSON Schema
        assert response.status_code == 200
        response_json = response.json()
        jsonschema.validate(instance=response_json, schema=LOGIN_SUCCESS_CONTRACT_SCHEMA)
        assert response_json["user"]["email"] == user_email
        assert response_json["user"]["role"] == "ANALYST"

    def test_auth_login_invalid_credentials_returns_401_and_error_schema(self, live_server):
        """Valida que credenciales inválidas retornen HTTP 401 y el contrato de error."""
        # Arrange
        url = f"{live_server.url}/api/v1/auth/login/"
        invalid_payload = {"email": "no_existe@banco.com", "password": "WrongPassword123!"}

        # Act
        response = requests.post(
            url,
            data=json.dumps(invalid_payload),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        # Assert: HTTP 401
        assert response.status_code == 401
        error_json = response.json()
        jsonschema.validate(instance=error_json, schema=ERROR_CONTRACT_SCHEMA)

    def test_non_existent_endpoint_returns_404(self, live_server):
        """Valida que rutas no existentes retornen código HTTP 404."""
        # Arrange
        url = f"{live_server.url}/api/v1/non-existent-route-404/"

        # Act
        response = requests.get(url, timeout=5)

        # Assert
        assert response.status_code == 404

    def test_company_lookup_contract_with_requests_and_auth(self, live_server):
        """Valida endpoint protegido de consulta de empresa con token JWT y schema."""
        # Arrange: Crear empresa y usuario analista
        CompanyProfile.objects.create(
            nit="800197268-4",
            legal_name="BANCOLOMBIA S.A.",
            ciiu="6412",
        )
        analyst = CustomUser.objects.create_user(
            email="analyst_lookup@banco.com",
            password="Password123!",
            role=Role.ANALYST,
        )

        # Obtener token
        login_res = requests.post(
            f"{live_server.url}/api/v1/auth/login/",
            json={"email": "analyst_lookup@banco.com", "password": "Password123!"},
            timeout=5,
        )
        token = login_res.json()["access"]
        lookup_url = f"{live_server.url}/api/v1/companies/lookup/?nit=800197268-4"

        # Act: Petición autenticada con requests
        response = requests.get(
            lookup_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )

        # Assert: HTTP 200 y validación de contrato
        assert response.status_code == 200
        data = response.json()
        jsonschema.validate(instance=data, schema=COMPANY_LOOKUP_CONTRACT_SCHEMA)
        assert data["nit"] == "800197268-4"
        assert data["legal_name"] == "BANCOLOMBIA S.A."

