from django.db import models
from django.conf import settings


class SoftDeleteQuerySet(models.QuerySet):
	def delete(self):
		return super().update(is_deleted=True)

	def hard_delete(self):
		return super().delete()

	def alive(self):
		return self.filter(is_deleted=False)


class SoftDeleteModel(models.Model):
	is_deleted = models.BooleanField(default=False)

	objects = SoftDeleteQuerySet.as_manager()

	class Meta:
		abstract = True


class Control(SoftDeleteModel):
	STATUS_IMPLEMENTED = 'implemented'
	STATUS_NOT_IMPLEMENTED = 'not_implemented'
	STATUS_CHOICES = [
		(STATUS_IMPLEMENTED, 'implemented'),
		(STATUS_NOT_IMPLEMENTED, 'not implemented'),
	]

	name = models.CharField(max_length=255)
	company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE, related_name='controls')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='controls_created')
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_IMPLEMENTED)

	def __str__(self) -> str:
		return f"{self.name} ({self.company})"


class Evidence(SoftDeleteModel):
	STATUS_APPROVED = 'approved'
	STATUS_REJECTED = 'rejected'
	STATUS_CHOICES = [
		(STATUS_APPROVED, 'approved'),
		(STATUS_REJECTED, 'rejected'),
	]

	control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name='evidence')
	name = models.CharField(max_length=255)
	file = models.FileField(upload_to='evidence/')
	company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE, related_name='evidence')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='evidence_created')
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES)

	def __str__(self) -> str:
		return f"{self.name} -> {self.control.name}"
