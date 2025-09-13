from django.shortcuts import redirect
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from social_django.utils import psa
from social_core.exceptions import AuthAlreadyAssociated, AuthException


@api_view(['GET'])
@permission_classes([AllowAny])
def microsoft_login(request):
    """
    Initiate Azure AD OAuth2 login
    """
    return redirect('social:begin', backend='azuread-oauth2')


@api_view(['GET'])
@permission_classes([AllowAny])
def microsoft_callback(request):
    """
    Handle Azure AD OAuth2 callback
    """
    try:
        # This will be handled by social_django
        return redirect('social:complete', backend='azuread-oauth2')
    except (AuthAlreadyAssociated, AuthException) as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def social_auth_success(request):
    """
    Handle successful social authentication
    """
    if request.user.is_authenticated:
        return JsonResponse({
            'message': 'Login successful',
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'role': request.user.role,
                'company': request.user.company.name if request.user.company else None
            }
        })
    else:
        return JsonResponse({'error': 'Authentication failed'}, status=401)


@api_view(['GET'])
@permission_classes([AllowAny])
def social_auth_error(request):
    """
    Handle social authentication errors
    """
    return JsonResponse({'error': 'Authentication failed'}, status=401)
