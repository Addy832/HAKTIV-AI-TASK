from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    path('check/', views.check_evidence_compliance, name='check_compliance'),
    path('status/<int:evidence_id>/', views.get_compliance_status, name='compliance_status'),
    path('checks/', views.list_compliance_checks, name='list_checks'),
    path('retry/<int:compliance_check_id>/', views.retry_compliance_check, name='retry_check'),
    path('ai-status/', views.get_ai_status, name='ai_status'),
]
