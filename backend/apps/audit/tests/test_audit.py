import pytest
from apps.accounts.models import CustomUser, Role
from apps.accounts.permissions import IsAnalyst, IsCompanyUser, IsAdminUserRole
from apps.audit.services import log_action
from apps.audit.models import AuditLog, AuditAction


@pytest.mark.django_db
class TestPermissionsAndAudit:
    def setup_method(self):
        self.analyst = CustomUser.objects.create_user(
            email="analyst@test.com", password="pass", role=Role.ANALYST
        )
        self.company = CustomUser.objects.create_user(
            email="company@test.com", password="pass", role=Role.COMPANY
        )
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com", password="pass", role=Role.ADMIN
        )

    def test_permission_matrix(self):
        class MockRequest:
            def __init__(self, user):
                self.user = user

        analyst_req = MockRequest(self.analyst)
        company_req = MockRequest(self.company)
        admin_req = MockRequest(self.admin)

        p_analyst = IsAnalyst()
        p_company = IsCompanyUser()
        p_admin = IsAdminUserRole()

        # IsAnalyst permissions
        assert p_analyst.has_permission(analyst_req, None) is True
        assert p_analyst.has_permission(company_req, None) is False
        assert p_analyst.has_permission(admin_req, None) is True

        # IsCompanyUser permissions
        assert p_company.has_permission(analyst_req, None) is False
        assert p_company.has_permission(company_req, None) is True
        assert p_company.has_permission(admin_req, None) is True

        # IsAdminUserRole permissions
        assert p_admin.has_permission(analyst_req, None) is False
        assert p_admin.has_permission(company_req, None) is False
        assert p_admin.has_permission(admin_req, None) is True

    def test_audit_logging_service(self):
        log_entry = log_action(
            user=self.analyst,
            action=AuditAction.SEARCH_NIT,
            entity="CompanyProfile",
            entity_id="900123456-7",
            metadata={"source": "OpenData"},
        )
        assert log_entry.pk is not None
        assert log_entry.user == self.analyst
        assert log_entry.action == AuditAction.SEARCH_NIT
        assert log_entry.entity_id == "900123456-7"
        assert AuditLog.objects.count() == 1
