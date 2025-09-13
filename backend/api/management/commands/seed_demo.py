from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Company
from api.models import Control, Evidence


class Command(BaseCommand):
    help = "Seed demo data: company, users, controls, evidence"

    def handle(self, *args, **options):
        User = get_user_model()

        company, _ = Company.objects.get_or_create(name="Acme Corp")

        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "company": company,
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not admin.password:
            admin.set_password("admin123")
            admin.save()

        employee, _ = User.objects.get_or_create(
            username="employee",
            defaults={
                "email": "employee@example.com",
                "company": company,
                "role": "employee",
            },
        )
        if not employee.password:
            employee.set_password("employee123")
            employee.save()

        mfa = Control.objects.alive().filter(name="MFA Control", company=company).first()
        if not mfa:
            mfa = Control.objects.create(
                name="MFA Control",
                company=company,
                created_by=admin,
                status=Control.STATUS_NOT_IMPLEMENTED,
            )

        sso = Control.objects.alive().filter(name="SSO Login Control", company=company).first()
        if not sso:
            sso = Control.objects.create(
                name="SSO Login Control",
                company=company,
                created_by=admin,
                status=Control.STATUS_NOT_IMPLEMENTED,
            )

        Evidence.objects.get_or_create(
            control=mfa,
            defaults={
                "name": "MFA Screenshot Placeholder",
                "file": "",
                "company": company,
                "created_by": admin,
                "status": Evidence.STATUS_REJECTED,
            },
        )

        Evidence.objects.get_or_create(
            control=sso,
            defaults={
                "name": "SSO Screenshot Placeholder",
                "file": "",
                "company": company,
                "created_by": admin,
                "status": Evidence.STATUS_REJECTED,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))


