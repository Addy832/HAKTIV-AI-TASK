from social_core.backends.azuread import AzureADOAuth2
from social_core.exceptions import AuthMissingParameter


class AzureADMultiTenantOAuth2(AzureADOAuth2):
    """
    Custom Azure AD OAuth2 backend for multi-tenant support that handles both UPN and email.
    """
    
    def get_redirect_uri(self, state=None):
        """
        Override to force the redirect URI to use localhost:8000
        """
        return 'http://localhost:8000/auth/complete/azuread-oauth2/'
    
    def auth_url(self):
        """
        Override to add prompt=login parameter to force credential entry every time
        """
        url = super().auth_url()
        # Add prompt=login to force authentication every time
        if '?' in url:
            url += '&prompt=login'
        else:
            url += '?prompt=login'
        return url
    
    def get_user_id(self, details, response):
        """
        Override to handle multi-tenant Azure AD by accepting either upn or email.
        Multi-tenant apps sometimes return email instead of upn depending on the user's directory.
        """
        # Use upn if available, fallback to email
        user_id = response.get('upn') or response.get('email')
        if not user_id:
            raise AuthMissingParameter(self, 'upn/email')
        return user_id
