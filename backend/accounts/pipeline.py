from social_core.pipeline.user import get_username
from .models import Company, User


def assign_company(strategy, details, user=None, *args, **kwargs):
    """
    Assign a company to the user based on their email domain or create a default company.
    This is called during the social authentication pipeline.
    """
    if user and not user.company:
        # Get email domain
        email = details.get('email', '')
        if email:
            domain = email.split('@')[1] if '@' in email else 'default.com'
            
            # Try to find existing company by domain
            company, company_created = Company.objects.get_or_create(
                name=f"{domain.title()} Corp",
                defaults={'is_deleted': False}
            )
            
            # Assign company to user
            user.company = company
            user.save()
            
            # Set default role based on email domain or admin status
            if not user.role:
                if 'admin' in email.lower() or 'administrator' in email.lower():
                    user.role = "admin"
                    user.is_staff = True
                else:
                    user.role = "employee"
                user.save()
            
            # If this is a new company, create default controls
            if company_created:
                from api.models import Control
                from django.contrib.auth import get_user_model
                
                # Create default controls for the new company
                Control.objects.create(
                    name="MFA Control - OTP Authentication",
                    company=company,
                    status=Control.STATUS_NOT_IMPLEMENTED,
                    created_by=user,
                    is_deleted=False
                )
                
                Control.objects.create(
                    name="SSO Login Control - Microsoft Azure AD",
                    company=company,
                    status=Control.STATUS_NOT_IMPLEMENTED,
                    created_by=user,
                    is_deleted=False
                )
    
    return kwargs
