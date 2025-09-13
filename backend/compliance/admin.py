from django.contrib import admin
from .models import ComplianceCheck


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ("id", "evidence", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at", "evidence__company")
    search_fields = ("evidence__name", "evidence__control__name")
    readonly_fields = ("created_at", "updated_at", "ai_analysis")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("evidence", "status", "created_at", "updated_at")
        }),
        ("AI Analysis", {
            "fields": ("ai_analysis", "rejection_reason", "recommendations"),
            "classes": ("collapse",)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "employee" and request.user.company:
            return qs.filter(evidence__company=request.user.company)
        return qs
    
    def has_add_permission(self, request, obj=None):
        return request.user.role == "admin"
    
    def has_change_permission(self, request, obj=None):
        if request.user.role == "admin":
            return True
        elif request.user.role == "employee" and request.user.company:
            if obj and hasattr(obj, 'evidence') and hasattr(obj.evidence, 'company'):
                return obj.evidence.company == request.user.company
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role == "admin"