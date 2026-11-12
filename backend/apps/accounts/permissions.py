import logging
from rest_framework.permissions import BasePermission
from apps.accounts.models import Role
from apps.companies.models import CompanyMembership, CompanyProfile

logger = logging.getLogger("apps.accounts.permissions")


def user_can_access_company(user, company: CompanyProfile) -> bool:
    """
    Returns True if the user is ADMIN/ANALYST, or if the user has role COMPANY
    with an APPROVED membership for the target company.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.role in [Role.ADMIN, Role.ANALYST]:
        return True
    if user.role == Role.COMPANY:
        has_membership = CompanyMembership.objects.filter(
            user=user, company=company, status="APPROVED"
        ).exists()
        if not has_membership:
            logger.warning(
                "Object permission denied: COMPANY user_id=%s attempted to access company_id=%s (nit=%s)",
                user.id,
                company.id,
                company.nit,
            )
        return has_membership
    return False


class IsAnalyst(BasePermission):
    """Permite el acceso a usuarios con rol Analista o Administrador."""

    def has_permission(self, request, view):
        allowed = bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role in [Role.ANALYST, Role.ADMIN] or request.user.is_superuser)
        )
        if not allowed and request.user and request.user.is_authenticated:
            logger.warning(
                "Permission denied (IsAnalyst): user_id=%s role=%s on %s",
                request.user.id,
                request.user.role,
                getattr(request, "path", "UNKNOWN"),
            )
        return allowed


class IsCompanyUser(BasePermission):
    """Permite el acceso a usuarios con rol Empresa o Administrador."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role in [Role.COMPANY, Role.ADMIN] or request.user.is_superuser)
        )


class IsAdminUserRole(BasePermission):
    """Permite el acceso exclusivamente a Administradores."""

    def has_permission(self, request, view):
        allowed = bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == Role.ADMIN or request.user.is_superuser)
        )
        if not allowed and request.user and request.user.is_authenticated:
            logger.warning(
                "Permission denied (IsAdminUserRole): user_id=%s role=%s on %s",
                request.user.id,
                request.user.role,
                getattr(request, "path", "UNKNOWN"),
            )
        return allowed


class IsCompanyAuthorizedObjectPermission(BasePermission):
    """
    Object-level permission ensuring a COMPANY user can only access their own
    approved CompanyProfile or entities tied to that CompanyProfile.
    """

    message = "El usuario Empresa solo tiene permiso para acceder a información de su propio NIT aprobado."

    def has_object_permission(self, request, view, obj):
        company = obj if isinstance(obj, CompanyProfile) else getattr(obj, "company", None)
        if company is None:
            return False
        return user_can_access_company(request.user, company)
