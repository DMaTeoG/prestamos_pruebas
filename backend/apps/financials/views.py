import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import user_can_access_company
from apps.companies.models import CompanyProfile
from apps.financials.models import FinancialStatement, StatementOrigin
from apps.financials.serializers import FinancialStatementSerializer, CSVImportSerializer
from apps.audit.services import log_action
from apps.audit.models import AuditAction

logger = logging.getLogger("apps.financials.views")


class FinancialStatementListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FinancialStatementSerializer
    pagination_class = None

    def get_company(self):
        company = get_object_or_404(CompanyProfile, pk=self.kwargs["company_id"])
        if not user_can_access_company(self.request.user, company):
            raise PermissionDenied(
                detail="El usuario Empresa solo puede consultar o cargar estados financieros de su propio NIT aprobado."
            )
        return company

    def get_queryset(self):
        company = self.get_company()
        return FinancialStatement.objects.filter(company=company).order_by("-fiscal_year")

    def create(self, request, *args, **kwargs):
        company = self.get_company()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fiscal_year = serializer.validated_data["fiscal_year"]
        origin = StatementOrigin.COMPANY if request.user.role == "COMPANY" else StatementOrigin.PUBLIC

        statement, _ = FinancialStatement.objects.update_or_create(
            company=company,
            fiscal_year=fiscal_year,
            defaults={
                "revenue": serializer.validated_data["revenue"],
                "expenses": serializer.validated_data["expenses"],
                "operating_income": serializer.validated_data["operating_income"],
                "net_income": serializer.validated_data["net_income"],
                "total_assets": serializer.validated_data["total_assets"],
                "current_assets": serializer.validated_data["current_assets"],
                "total_liabilities": serializer.validated_data["total_liabilities"],
                "current_liabilities": serializer.validated_data["current_liabilities"],
                "financial_debt": serializer.validated_data.get("financial_debt", Decimal("0")),
                "financial_expenses": serializer.validated_data.get("financial_expenses", Decimal("0")),
                "uploaded_by": request.user,
                "origin": origin,
            },
        )

        log_action(
            user=request.user,
            action=AuditAction.FINANCIAL_STATEMENT_UPLOAD,
            entity="FinancialStatement",
            entity_id=statement.id,
            request=request,
            metadata={"fiscal_year": statement.fiscal_year, "company_id": company.id},
        )
        logger.info(
            "Financial statement saved: user_id=%s company_id=%s fiscal_year=%s",
            request.user.id,
            company.id,
            statement.fiscal_year,
        )

        output_serializer = self.get_serializer(statement)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class FinancialStatementCSVImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        company = get_object_or_404(CompanyProfile, pk=company_id)
        if not user_can_access_company(request.user, company):
            return Response(
                {
                    "code": "FORBIDDEN",
                    "message": "El usuario Empresa solo puede cargar archivos CSV para su propio NIT aprobado.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data["file"]
        try:
            decoded_file = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            logger.error("CSV decode error for company_id=%s: %s", company.id, str(exc))
            return Response(
                {"code": "CSV_ENCODING_ERROR", "message": "El archivo CSV debe estar codificado en UTF-8."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created_statements = []
        for row_idx, row in enumerate(reader, start=1):
            try:
                fiscal_year = int(row["fiscal_year"])
                stmt, _ = FinancialStatement.objects.update_or_create(
                    company=company,
                    fiscal_year=fiscal_year,
                    defaults={
                        "revenue": Decimal(str(row.get("revenue", 0))),
                        "expenses": Decimal(str(row.get("expenses", 0))),
                        "operating_income": Decimal(str(row.get("operating_income", 0))),
                        "net_income": Decimal(str(row.get("net_income", 0))),
                        "total_assets": Decimal(str(row.get("total_assets", 0))),
                        "current_assets": Decimal(str(row.get("current_assets", 0))),
                        "total_liabilities": Decimal(str(row.get("total_liabilities", 0))),
                        "current_liabilities": Decimal(str(row.get("current_liabilities", 0))),
                        "financial_debt": Decimal(str(row.get("financial_debt", 0))),
                        "financial_expenses": Decimal(str(row.get("financial_expenses", 0))),
                        "uploaded_by": request.user,
                        "origin": StatementOrigin.COMPANY if request.user.role == "COMPANY" else StatementOrigin.PUBLIC,
                    },
                )
                created_statements.append(stmt.id)
            except (KeyError, ValueError, InvalidOperation) as exc:
                logger.warning(
                    "CSV parsing error on row %s for company_id=%s by user_id=%s: %s",
                    row_idx,
                    company.id,
                    request.user.id,
                    str(exc),
                )
                return Response(
                    {"code": "CSV_PARSING_ERROR", "message": f"Error al procesar fila {row_idx} del CSV: {str(exc)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        log_action(
            user=request.user,
            action=AuditAction.FINANCIAL_STATEMENT_UPLOAD,
            entity="CompanyProfile",
            entity_id=company.id,
            request=request,
            metadata={"created_count": len(created_statements), "method": "CSV"},
        )
        logger.info(
            "CSV financial statements imported: user_id=%s company_id=%s count=%s",
            request.user.id,
            company.id,
            len(created_statements),
        )

        return Response(
            {
                "message": f"Se importaron {len(created_statements)} estados financieros con éxito.",
                "imported_count": len(created_statements),
            },
            status=status.HTTP_201_CREATED,
        )
