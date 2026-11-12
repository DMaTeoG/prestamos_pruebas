import logging

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAdminUserRole,
    IsCompanyAuthorizedObjectPermission,
    user_can_access_company,
)
from apps.audit.models import AuditAction
from apps.audit.services import log_action
from apps.companies.models import CompanyMembership, CompanyProfile
from apps.companies.serializers import CompanyMembershipSerializer, CompanyProfileSerializer
from apps.companies.validators import validate_and_clean_nit
from apps.sources.services import OpenDataSource

logger = logging.getLogger("apps.companies.views")


class CompanyLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        nit_param = request.query_params.get("nit", "").strip()
        if not nit_param:
            return Response(
                {"code": "NIT_REQUIRED", "message": "Debe proporcionar el parámetro 'nit'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            nit_clean, dv = validate_and_clean_nit(nit_param)
        except Exception as exc:
            logger.warning(
                "NIT validation failed on lookup by user_id=%s: %s",
                request.user.id,
                str(exc),
            )
            return Response(
                {"code": "INVALID_NIT", "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce Company role restrictions: Company role can only look up its linked NIT
        if request.user.role == "COMPANY" and not request.user.is_superuser:
            membership = CompanyMembership.objects.filter(
                user=request.user, company__nit=nit_clean, status="APPROVED"
            ).first()
            if not membership:
                logger.warning(
                    "Forbidden NIT lookup by COMPANY user_id=%s for nit=%s",
                    request.user.id,
                    nit_clean,
                )
                return Response(
                    {"code": "FORBIDDEN", "message": "El usuario Empresa solo puede consultar su propio NIT autorizado."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        company = CompanyProfile.objects.filter(nit=nit_clean).first()
        if not company:
            source = OpenDataSource()
            info = source.fetch_company_info(nit_clean)
            if info:
                company = CompanyProfile.objects.create(
                    nit=info["nit"],
                    dv=info.get("dv", dv),
                    legal_name=info["legal_name"],
                    ciiu=info.get("ciiu", ""),
                    registration_date=info.get("registration_date"),
                    status=info.get("status", "ACTIVA"),
                    city=info.get("city", ""),
                    size=info.get("size", "MICRO"),
                )

        if not company:
            logger.warning("Company not found for nit=%s", nit_clean)
            return Response(
                {"code": "NOT_FOUND", "message": f"No se encontró información para el NIT {nit_clean}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        log_action(
            user=request.user,
            action=AuditAction.SEARCH_NIT,
            entity="CompanyProfile",
            entity_id=company.id,
            request=request,
            metadata={"nit": nit_clean},
        )
        logger.info("NIT lookup succeeded: user_id=%s nit=%s company_id=%s", request.user.id, nit_clean, company.id)

        serializer = CompanyProfileSerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsCompanyAuthorizedObjectPermission]
    serializer_class = CompanyProfileSerializer
    queryset = CompanyProfile.objects.all()


class MyCompanyView(APIView):
    """
    GET /api/v1/companies/my-company/
    Returns the approved CompanyProfile linked to the current COMPANY user
    (or the first company for Analyst/Admin preview).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "COMPANY" and not request.user.is_superuser:
            membership = (
                CompanyMembership.objects.filter(user=request.user, status="APPROVED")
                .select_related("company")
                .first()
            )
            if not membership:
                return Response(
                    {
                        "code": "NO_APPROVED_MEMBERSHIP",
                        "message": "No tienes ningún vínculo NIT aprobado por un Administrador todavía.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            company = membership.company
        else:
            company = CompanyProfile.objects.first()
            if not company:
                return Response(
                    {"code": "NOT_FOUND", "message": "No hay empresas registradas en el sistema."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        if not user_can_access_company(request.user, company):
            return Response(
                {"code": "FORBIDDEN", "message": "No autorizado para ver esta empresa."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CompanyProfileSerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminMembershipListView(generics.ListCreateAPIView):
    """GET/POST /api/v1/admin/memberships/ — Lista o crea vínculos Usuario-NIT (solo Admin)."""

    permission_classes = [IsAdminUserRole]
    serializer_class = CompanyMembershipSerializer
    queryset = CompanyMembership.objects.select_related("user", "company", "approved_by").order_by("-created_at")
    pagination_class = None


class AdminMembershipUpdateView(APIView):
    """PATCH /api/v1/admin/memberships/<pk>/ — Aprueba o rechaza vínculo Usuario-NIT (solo Admin)."""

    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        membership = generics.get_object_or_404(CompanyMembership, pk=pk)
        new_status = request.data.get("status", "APPROVED")
        if new_status not in ("APPROVED", "REJECTED", "PENDING"):
            return Response(
                {"code": "INVALID_STATUS", "message": "El estado debe ser APPROVED, REJECTED o PENDING."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.status = new_status
        membership.approved_by = request.user
        membership.save()

        log_action(
            user=request.user,
            action=AuditAction.MEMBERSHIP_APPROVAL,
            entity="CompanyMembership",
            entity_id=membership.id,
            request=request,
            metadata={
                "target_user": membership.user.email,
                "nit": membership.company.nit,
                "status": new_status,
            },
        )
        logger.info(
            "Membership updated by admin_id=%s: membership_id=%s status=%s nit=%s",
            request.user.id,
            membership.id,
            new_status,
            membership.company.nit,
        )

        serializer = CompanyMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_200_OK)
