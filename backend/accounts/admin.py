from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from .models import Company, User


class CompanyAdminMixin:
    """Mixin to restrict admin access based on user role and company"""
    
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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_deleted", "created_at")
    search_fields = ("name",)
    list_filter = ("is_deleted",)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "employee" and request.user.company:
            # Employees can only see their own company
            return qs.filter(id=request.user.company.id)
        return qs
    
    def has_add_permission(self, request, obj=None):
        # Only admins can add new companies
        return request.user.role == "admin"
    
    def has_change_permission(self, request, obj=None):
        if request.user.role == "admin":
            return True
        elif request.user.role == "employee" and request.user.company:
            # Employees can only change their own company
            if obj:
                return obj.id == request.user.company.id
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only admins can delete companies
        return request.user.role == "admin"


@admin.register(User)
class UserAdmin(CompanyAdminMixin, DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Organization", {"fields": ("company", "role")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Organization", {"fields": ("company", "role")}),
    )
    list_display = ("id", "username", "email", "company", "role", "is_staff")
    list_filter = ("company", "role", "is_staff")
    search_fields = ("username", "email", "company__name")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "employee" and request.user.company:
            # Employees can only see users from their own company
            return qs.filter(company=request.user.company)
        return qs


# Hide the default Group admin since we're using custom roles
admin.site.unregister(Group)


