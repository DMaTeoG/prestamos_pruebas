import csv
import io
from decimal import Decimal
from rest_framework import serializers
from apps.financials.models import FinancialStatement, StatementOrigin
from apps.financials.ratios import calculate_financial_ratios


class FinancialStatementSerializer(serializers.ModelSerializer):
    ratios = serializers.SerializerMethodField()

    class Meta:
        model = FinancialStatement
        fields = [
            "id",
            "company",
            "fiscal_year",
            "revenue",
            "expenses",
            "operating_income",
            "net_income",
            "total_assets",
            "current_assets",
            "total_liabilities",
            "current_liabilities",
            "financial_debt",
            "financial_expenses",
            "origin",
            "uploaded_by",
            "created_at",
            "ratios",
        ]
        read_only_fields = ["id", "company", "uploaded_by", "created_at", "ratios"]

    def get_ratios(self, obj):
        prev = FinancialStatement.objects.filter(
            company=obj.company, fiscal_year=obj.fiscal_year - 1
        ).first()
        return calculate_financial_ratios(obj, prev)


class CSVImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError("El archivo debe estar en formato CSV (.csv).")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("El tamaño máximo permitido es 5 MB.")
        return value
