from django.urls import path
from .views import ping, get_user, logout_view, list_controls, list_evidence, delete_evidence, upload_evidence, update_control_status, rag_webhook
from .social_views import microsoft_login, microsoft_callback, social_auth_success, social_auth_error


urlpatterns = [
    path('ping/', ping, name='ping'),
    path('user/', get_user, name='user'),
    path('logout/', logout_view, name='logout'),
    path('microsoft-login/', microsoft_login, name='microsoft-login'),
    path('microsoft-callback/', microsoft_callback, name='microsoft-callback'),
    path('social-success/', social_auth_success, name='social-success'),
    path('social-error/', social_auth_error, name='social-error'),
    path('control/', list_controls, name='control-list'),
    path('control/status/', update_control_status, name='control-status'),
    path('evidence/', list_evidence, name='evidence-list'),
    path('evidence/delete/', delete_evidence, name='evidence-delete'),
    path('evidence/upload/', upload_evidence, name='evidence-upload'),
    path('rag/webhook/', rag_webhook, name='rag-webhook'),
]


