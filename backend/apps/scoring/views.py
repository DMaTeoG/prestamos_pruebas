import logging

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAdminUserRole,
    IsCompanyAuthorizedObjectPermission,
)
from apps.audit.models import AuditAction
from apps.audit.services import log_action
from apps.companies.models import CompanyMembership, CompanyProfile
from apps.companies.validators import validate_and_clean_nit
from apps.scoring.models import Evaluation, ModelVersion
from apps.scoring.serializers import (
    EvaluationCreateSerializer,
    EvaluationDecisionSerializer,
    EvaluationDetailSerializer,
    ModelVersionSerializer,
)
from apps.scoring.services import (
    evaluate_company,
    get_active_model_version,
    record_credit_decision,
)

logger = logging.getLogger("apps.scoring.views")


class EvaluationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = Evaluation.objects.select_related(
            "company", "requested_by", "decided_by", "model_version"
        ).all()

        # Role restrictions
        if user.role == "COMPANY" and not user.is_superuser:
            memberships = CompanyMembership.objects.filter(
                user=user, status="APPROVED"
            ).values_list("company_id", flat=True)
            queryset = queryset.filter(company_id__in=memberships)

        # Filters (nit, risk_level, date_from, date_to)
        nit = request.query_params.get("nit")
        if nit:
            queryset = queryset.filter(company__nit__icontains=nit.strip())

        risk = request.query_params.get("risk_level")
        if risk:
            queryset = queryset.filter(risk_level=risk.strip().upper())

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        serializer = EvaluationDetailSerializer(queryset[:50], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EvaluationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nit_raw = serializer.validated_data["nit"]
        statement_id = serializer.validated_data.get("statement_id")
        requested_amount = serializer.validated_data.get("requested_amount")
        term_months = serializer.validated_data.get("term_months")

        try:
            nit_clean, _ = validate_and_clean_nit(nit_raw)
        except Exception as exc:
            logger.warning(
                "Invalid NIT on evaluation request by user_id=%s: %s",
                request.user.id,
                str(exc),
            )
            return Response(
                {"code": "INVALID_NIT", "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # COMPANY users can only request credit study/scoring for their own APPROVED NIT
        if request.user.role == "COMPANY" and not request.user.is_superuser:
            has_approved_membership = CompanyMembership.objects.filter(
                user=request.user,
                company__nit=nit_clean,
                status="APPROVED",
            ).exists()
            if not has_approved_membership:
                logger.warning(
                    "Forbidden evaluation request by COMPANY user_id=%s for nit=%s",
                    request.user.id,
                    nit_clean,
                )
                return Response(
                    {
                        "code": "FORBIDDEN",
                        "message": "El usuario con rol Empresa solo puede solicitar estudio de crédito para su propio NIT aprobado.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        company = CompanyProfile.objects.filter(nit=nit_clean).first()
        if not company:
            from apps.sources.services import OpenDataSource

            source = OpenDataSource()
            info = source.fetch_company_info(nit_clean)
            company = CompanyProfile.objects.create(
                nit=info["nit"],
                dv=info.get("dv", "7"),
                legal_name=info["legal_name"],
                ciiu=info.get("ciiu", ""),
                registration_date=info.get("registration_date"),
                status=info.get("status", "ACTIVA"),
                city=info.get("city", ""),
                size=info.get("size", "MICRO"),
            )

        statement = None
        if statement_id:
            statement = company.financial_statements.filter(pk=statement_id).first()

        evaluation = evaluate_company(
            company,
            request.user,
            statement=statement,
            request=request,
            requested_amount=requested_amount,
            term_months=term_months,
        )
        detail_serializer = EvaluationDetailSerializer(evaluation)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class EvaluationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsCompanyAuthorizedObjectPermission]
    serializer_class = EvaluationDetailSerializer
    queryset = Evaluation.objects.select_related("company", "requested_by", "model_version").all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.role == "ANALYST" and not user.is_superuser and obj.requested_by_id != user.id:
            logger.warning(
                "Object permission denied: ANALYST user_id=%s attempted to access evaluation_id=%s owned by user_id=%s",
                user.id,
                obj.id,
                obj.requested_by_id,
            )
            raise PermissionDenied(detail="El Analista solo puede consultar las evaluaciones que ha solicitado.")
        return obj


class AdminModelVersionListView(generics.ListAPIView):
    """GET /api/v1/admin/models/ — Lista todas las versiones de modelo ML (solo Admin)."""

    permission_classes = [IsAdminUserRole]
    serializer_class = ModelVersionSerializer
    pagination_class = None

    def get_queryset(self):
        if not ModelVersion.objects.exists():
            get_active_model_version()
        return ModelVersion.objects.all().order_by("-trained_at")


class AdminModelActivateView(APIView):
    """POST /api/v1/admin/models/<pk>/activate/ — Activa una versión de modelo ML (solo Admin)."""

    permission_classes = [IsAdminUserRole]

    def post(self, request, pk):
        model_version = generics.get_object_or_404(ModelVersion, pk=pk)
        model_version.is_active = True
        model_version.save()

        log_action(
            user=request.user,
            action=AuditAction.MODEL_ACTIVATION,
            entity="ModelVersion",
            entity_id=model_version.id,
            request=request,
            metadata={"version": model_version.version, "algorithm": model_version.algorithm},
        )
        logger.info(
            "Model version activated by admin_id=%s: version=%s (id=%s)",
            request.user.id,
            model_version.version,
            model_version.id,
        )

        serializer = ModelVersionSerializer(model_version)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminEvaluationDecisionView(APIView):
    """
    PATCH /api/v1/admin/evaluations/<pk>/decision/
    Permite al Administrador registrar la decisión manual de comité (APPROVED o REJECTED)
    apoyado en el Score y explicación SHAP de la evaluación (solo Admin).
    """

    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        evaluation = generics.get_object_or_404(
            Evaluation.objects.select_related("company", "requested_by", "decided_by", "model_version"),
            pk=pk,
        )
        serializer = EvaluationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = record_credit_decision(
            evaluation=evaluation,
            admin_user=request.user,
            decision_status=serializer.validated_data["decision_status"],
            request=request,
        )
        return Response(EvaluationDetailSerializer(updated).data, status=status.HTTP_200_OK)
