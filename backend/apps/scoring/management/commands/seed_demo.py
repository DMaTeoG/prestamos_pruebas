from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser, Role
from apps.companies.models import CompanyProfile, CompanyMembership, CompanySize, MembershipStatus
from apps.financials.models import FinancialStatement, StatementOrigin
from apps.scoring.services import evaluate_company, get_active_model_version


class Command(BaseCommand):
    help = "Seeds demo users (ANALYST, COMPANY, ADMIN), companies, financial statements, memberships, and initial evaluation (T7.5)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data for Sistema Web Inteligente de Scoring Empresarial...")

        # 1. Create or update demo users for all 3 roles
        admin_user, _ = CustomUser.objects.update_or_create(
            email="admin.demo@banco.com",
            defaults={
                "first_name": "Laura",
                "last_name": "Administradora",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin_user.set_password("Password123!")
        admin_user.save()

        analyst_user, _ = CustomUser.objects.update_or_create(
            email="analista.demo@banco.com",
            defaults={
                "first_name": "Carlos",
                "last_name": "Analista",
                "role": Role.ANALYST,
                "is_active": True,
            },
        )
        analyst_user.set_password("Password123!")
        analyst_user.save()

        company_user, _ = CustomUser.objects.update_or_create(
            email="empresa.demo@empresa.com",
            defaults={
                "first_name": "Representante",
                "last_name": "Empresa",
                "role": Role.COMPANY,
                "is_active": True,
            },
        )
        company_user.set_password("Password123!")
        company_user.save()

        pending_user, _ = CustomUser.objects.update_or_create(
            email="pendiente.demo@empresa.com",
            defaults={
                "first_name": "Solicitante",
                "last_name": "Pendiente",
                "role": Role.COMPANY,
                "is_active": True,
            },
        )
        pending_user.set_password("Password123!")
        pending_user.save()

        # 2. Create demo companies with valid NIT + DV
        comp_main, _ = CompanyProfile.objects.update_or_create(
            nit="800197268-4",
            defaults={
                "dv": "4",
                "legal_name": "BANCOLOMBIA S.A.",
                "ciiu": "6412",
                "registration_date": "1998-01-24",
                "status": "ACTIVA",
                "city": "Medellín",
                "size": CompanySize.GRANDE,
            },
        )

        comp_secondary, _ = CompanyProfile.objects.update_or_create(
            nit="900123456-8",
            defaults={
                "dv": "8",
                "legal_name": "EMPRESA SIMULADA COLOMBIA S.A.S.",
                "ciiu": "4690",
                "registration_date": "2019-06-15",
                "status": "ACTIVA",
                "city": "Bogotá, D.C.",
                "size": CompanySize.MEDIANA,
            },
        )

        # 3. Create memberships (one APPROVED, one PENDING for Admin demo)
        CompanyMembership.objects.update_or_create(
            user=company_user,
            company=comp_main,
            defaults={
                "status": MembershipStatus.APPROVED,
                "approved_by": admin_user,
            },
        )
        CompanyMembership.objects.update_or_create(
            user=pending_user,
            company=comp_secondary,
            defaults={
                "status": MembershipStatus.PENDING,
            },
        )

        # 4. Seed Financial Statements (2022 & 2023)
        FinancialStatement.objects.update_or_create(
            company=comp_main,
            fiscal_year=2022,
            defaults={
                "revenue": Decimal("1150000000.00"),
                "expenses": Decimal("820000000.00"),
                "operating_income": Decimal("330000000.00"),
                "net_income": Decimal("220000000.00"),
                "total_assets": Decimal("1450000000.00"),
                "current_assets": Decimal("580000000.00"),
                "total_liabilities": Decimal("520000000.00"),
                "current_liabilities": Decimal("290000000.00"),
                "financial_debt": Decimal("210000000.00"),
                "financial_expenses": Decimal("42000000.00"),
                "origin": StatementOrigin.COMPANY,
                "uploaded_by": company_user,
            },
        )
        stmt_2023, _ = FinancialStatement.objects.update_or_create(
            company=comp_main,
            fiscal_year=2023,
            defaults={
                "revenue": Decimal("1350000000.00"),
                "expenses": Decimal("910000000.00"),
                "operating_income": Decimal("440000000.00"),
                "net_income": Decimal("310000000.00"),
                "total_assets": Decimal("1680000000.00"),
                "current_assets": Decimal("690000000.00"),
                "total_liabilities": Decimal("540000000.00"),
                "current_liabilities": Decimal("300000000.00"),
                "financial_debt": Decimal("195000000.00"),
                "financial_expenses": Decimal("39000000.00"),
                "origin": StatementOrigin.COMPANY,
                "uploaded_by": company_user,
            },
        )

        # 5. Register active model & run initial evaluation
        model_ver = get_active_model_version()
        evaluation = evaluate_company(comp_main, analyst_user, statement=stmt_2023)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo seed complete! Active model: {model_ver.version} | Initial Evaluation #{evaluation.id} Score: {evaluation.score} ({evaluation.risk_level})"
            )
        )
