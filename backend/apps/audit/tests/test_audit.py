import pytest

from apps.accounts.models import CustomUser, Role
from apps.accounts.permissions import IsAdminUserRole, IsAnalyst, IsCompanyUser
from apps.audit.models import AuditAction, AuditLog
from apps.audit.services import log_action

# ==============================================================================
# Semana 1: Patrón AAA (Arrange, Act, Assert) en Permisos y Auditoría
# ==============================================================================


@pytest.mark.django_db
class TestPermissionsAndAudit:
    def setup_method(self):
        # Arrange global de usuarios
        self.analyst = CustomUser.objects.create_user(
            email="analyst@test.com", password="pass", role=Role.ANALYST
        )
        self.company = CustomUser.objects.create_user(
            email="company@test.com", password="pass", role=Role.COMPANY
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com", password="pass", role=Role.ADMIN
        )

    def test_permission_matrix_aaa(self):
        """Verifica la matriz de permisos RBAC bajo el patrón AAA."""
        # Arrange
        class MockRequest:
            def __init__(self, user):
                self.user = user

        analyst_req = MockRequest(self.analyst)
        company_req = MockRequest(self.company)
        admin_req = MockRequest(self.admin)

        p_analyst = IsAnalyst()
        p_company = IsCompanyUser()
        p_admin = IsAdminUserRole()

        # Act & Assert: IsAnalyst permissions
        assert p_analyst.has_permission(analyst_req, None) is True
        assert p_analyst.has_permission(company_req, None) is False
        assert p_analyst.has_permission(admin_req, None) is True

        # Act & Assert: IsCompanyUser permissions
        assert p_company.has_permission(analyst_req, None) is False
        assert p_company.has_permission(company_req, None) is True
        assert p_company.has_permission(admin_req, None) is True

        # Act & Assert: IsAdminUserRole permissions
        assert p_admin.has_permission(analyst_req, None) is False
        assert p_admin.has_permission(company_req, None) is False
        assert p_admin.has_permission(admin_req, None) is True

    def test_audit_logging_service_aaa(self):
        """Valida el registro de trazabilidad en base de datos con AAA."""
        # Arrange
        acting_user = self.analyst
        action_type = AuditAction.SEARCH_NIT
        target_entity = "CompanyProfile"
        entity_id = "900123456-7"
        extra_metadata = {"source": "OpenData"}

        # Act: Registro de la acción de auditoría
        log_entry = log_action(
            user=acting_user,
            action=action_type,
            entity=target_entity,
            entity_id=entity_id,
            metadata=extra_metadata,
        )

        # Assert: Verificación de persistencia y atributos
        assert log_entry.pk is not None
        assert log_entry.user == acting_user
        assert log_entry.action == action_type
        assert log_entry.entity_id == entity_id
        assert AuditLog.objects.count() == 1
