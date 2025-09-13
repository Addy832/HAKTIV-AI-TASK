from django.db import models
from django.contrib.auth import get_user_model
from api.models import Control, Evidence

User = get_user_model()


class ComplianceCheck(models.Model):
    """Model to track compliance checks performed on evidence"""
    
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_ERROR = "error"
    
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_ERROR, "Error"),
    ]
    
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name='compliance_check')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    ai_analysis = models.JSONField(null=True, blank=True, help_text="AI analysis results")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    recommendations = models.TextField(blank=True, help_text="AI recommendations for improvement")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Compliance Check for {self.evidence.name} - {self.status}"

