from rest_framework import serializers
from apps.companies.models import CompanyProfile, CompanyMembership


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            "id",
            "nit",
            "dv",
            "legal_name",
            "ciiu",
            "registration_date",
            "status",
            "city",
            "size",
            "last_synced_at",
            "created_at",
        ]
        read_only_fields = ["id", "last_synced_at", "created_at"]


class CompanyMembershipSerializer(serializers.ModelSerializer):
    company_detail = CompanyProfileSerializer(source="company", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CompanyMembership
        fields = [
            "id",
            "user",
            "user_email",
            "company",
            "company_detail",
            "status",
            "approved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "approved_by", "created_at", "updated_at"]
