from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Company
from api.models import Control


class Command(BaseCommand):
    help = "Seed default control data for compliance management"

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get or create a default company
        company, created = Company.objects.get_or_create(
            name="Default Company",
            defaults={'is_deleted': False}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created company: {company.name}"))
        else:
            self.stdout.write(f"Using existing company: {company.name}")
        
        # Get or create a default admin user
        admin, created = User.objects.get_or_create(
            username="default_admin",
            defaults={
                "email": "admin@defaultcompany.com",
                "company": company,
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Default",
                "last_name": "Admin"
            },
        )
        
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created admin user: {admin.username}"))
        else:
            self.stdout.write(f"Using existing admin user: {admin.username}")

        # Create controls for ALL companies
        all_companies = Company.objects.filter(is_deleted=False)
        total_controls_created = 0
        
        for company in all_companies:
            self.stdout.write(f"Processing company: {company.name}")
            
            # Get or create admin user for this company
            company_admin, admin_created = User.objects.get_or_create(
                username=f"admin_{company.name.lower().replace(' ', '_')}",
                defaults={
                    "email": f"admin@{company.name.lower().replace(' ', '_')}.com",
                    "company": company,
                    "role": "admin",
                    "is_staff": True,
                    "is_superuser": True,
                    "first_name": "Admin",
                    "last_name": company.name
                },
            )
            
            if admin_created:
                company_admin.set_password("admin123")
                company_admin.save()
                self.stdout.write(f"Created admin user for {company.name}")
            
            # Create MFA Control for this company
            mfa_control, mfa_created = Control.objects.get_or_create(
                name="MFA Control - OTP Authentication",
                company=company,
                defaults={
                    "status": Control.STATUS_NOT_IMPLEMENTED,
                    "created_by": company_admin,
                    "is_deleted": False
                }
            )
            
            if mfa_created:
                self.stdout.write(self.style.SUCCESS(f"Created MFA Control for {company.name}"))
                total_controls_created += 1
            else:
                self.stdout.write(f"MFA Control already exists for {company.name}")

            # Create SSO Control for this company
            sso_control, sso_created = Control.objects.get_or_create(
                name="SSO Login Control - Microsoft Azure AD",
                company=company,
                defaults={
                    "status": Control.STATUS_NOT_IMPLEMENTED,
                    "created_by": company_admin,
                    "is_deleted": False
                }
            )
            
            if sso_created:
                self.stdout.write(self.style.SUCCESS(f"Created SSO Control for {company.name}"))
                total_controls_created += 1
            else:
                self.stdout.write(f"SSO Control already exists for {company.name}")

        self.stdout.write(self.style.SUCCESS("✅ Default control data seeded successfully!"))
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   • Companies processed: {all_companies.count()}")
        self.stdout.write(f"   • Controls created: {total_controls_created}")
        self.stdout.write(f"\n📋 Default Controls for each company:")
        self.stdout.write(f"   1. MFA Control - OTP Authentication")
        self.stdout.write(f"      → Screenshot should display an OTP login window")
        self.stdout.write(f"   2. SSO Login Control - Microsoft Azure AD")
        self.stdout.write(f"      → Screenshot should display Microsoft Azure SSO login")
        self.stdout.write(f"\n👤 Admin Users: admin_[company_name] / admin123")
        self.stdout.write(f"🏢 Companies: {', '.join([c.name for c in all_companies])}")
