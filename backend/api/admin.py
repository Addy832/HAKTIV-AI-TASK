from django.contrib import admin
from .models import Control, Evidence


class APIAdminMixin:
    """Mixin to restrict API admin access based on user role and company"""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "employee" and request.user.company:
            # Employees can only see their own company's data
            return qs.filter(company=request.user.company)
        return qs
    
    def has_add_permission(self, request, obj=None):
        # Only admins can add new records
        return request.user.role == "admin"
    
    def has_change_permission(self, request, obj=None):
        if request.user.role == "admin":
            return True
        elif request.user.role == "employee" and request.user.company:
            # Employees can only change records from their own company
            if obj and hasattr(obj, 'company'):
                return obj.company == request.user.company
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only admins can delete records
        return request.user.role == "admin"


@admin.register(Control)
class ControlAdmin(APIAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "company", "status", "created_by", "created_at", "is_deleted")
    list_filter = ("status", "company", "is_deleted")
    search_fields = ("name",)

    actions = [
        "mark_implemented",
    ]

    def mark_implemented(self, request, queryset):
        # Only admins can use bulk actions
        if request.user.role != "admin":
            self.message_user(request, "Only admins can perform bulk actions.", level='ERROR')
            return
        queryset.update(status=Control.STATUS_IMPLEMENTED)
        self.message_user(request, f"Marked {queryset.count()} controls as implemented.")
    mark_implemented.short_description = "Mark selected controls implemented"


@admin.register(Evidence)
class EvidenceAdmin(APIAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "control", "company", "status", "created_by", "created_at", "is_deleted")
    list_filter = ("status", "company", "is_deleted")
    search_fields = ("name",)

    actions = [
        "soft_delete",
    ]

    def soft_delete(self, request, queryset):
        # Only admins can use bulk actions
        if request.user.role != "admin":
            self.message_user(request, "Only admins can perform bulk actions.", level='ERROR')
            return
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Soft deleted {count} evidence records.")
    soft_delete.short_description = "Soft delete selected evidence"


