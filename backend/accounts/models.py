from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=[("admin", "admin"), ("employee", "employee")], default="employee")


