from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging

from .models import ComplianceCheck
from .services import ComplianceAIService, MockAIService

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def check_evidence_compliance(request):
    """Check compliance for uploaded evidence"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication credentials were not provided."}, status=403)
    
    try:
        data = json.loads(request.body)
        evidence_id = data.get('evidence_id')
        
        if not evidence_id:
            return JsonResponse({"error": "evidence_id is required"}, status=400)
        
        # Use real AI service if configured, otherwise fall back to mock
        try:
            ai_service = ComplianceAIService()
            compliance_check = ai_service.check_compliance(evidence_id)
        except Exception as e:
            # Fall back to mock service if AI is not configured
            ai_service = MockAIService()
            compliance_check = ai_service.check_compliance(evidence_id)
        
        return JsonResponse({
            "compliance_check_id": compliance_check.id,
            "status": compliance_check.status,
            "ai_analysis": compliance_check.ai_analysis,
            "rejection_reason": compliance_check.rejection_reason,
            "recommendations": compliance_check.recommendations
        })
        
    except Exception as e:
        logger.error(f"Compliance check failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def get_compliance_status(request, evidence_id):
    """Get compliance status for specific evidence"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication credentials were not provided."}, status=403)
    
    try:
        compliance_check = ComplianceCheck.objects.get(evidence_id=evidence_id)
        
        return JsonResponse({
            "compliance_check_id": compliance_check.id,
            "status": compliance_check.status,
            "ai_analysis": compliance_check.ai_analysis,
            "rejection_reason": compliance_check.rejection_reason,
            "recommendations": compliance_check.recommendations,
            "created_at": compliance_check.created_at.isoformat(),
            "updated_at": compliance_check.updated_at.isoformat()
        })
        
    except ComplianceCheck.DoesNotExist:
        return JsonResponse({"error": "Compliance check not found"}, status=404)
    except Exception as e:
        logger.error(f"Failed to get compliance status: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def list_compliance_checks(request):
    """List all compliance checks for the user's company"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication credentials were not provided."}, status=403)
    
    try:
        # Filter by user's company
        company = request.user.company
        if not company:
            return JsonResponse({"error": "User not assigned to a company"}, status=400)
        
        checks = ComplianceCheck.objects.filter(
            evidence__company=company
        ).select_related('evidence', 'evidence__control')
        
        results = []
        for check in checks:
            results.append({
                "id": check.id,
                "evidence_id": check.evidence.id,
                "evidence_name": check.evidence.name,
                "control_name": check.evidence.control.name,
                "status": check.status,
                "ai_analysis": check.ai_analysis,
                "rejection_reason": check.rejection_reason,
                "recommendations": check.recommendations,
                "created_at": check.created_at.isoformat(),
                "updated_at": check.updated_at.isoformat()
            })
        
        return JsonResponse({"compliance_checks": results})
        
    except Exception as e:
        logger.error(f"Failed to list compliance checks: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def retry_compliance_check(request, compliance_check_id):
    """Retry a failed compliance check"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication credentials were not provided."}, status=403)
    
    try:
        compliance_check = ComplianceCheck.objects.get(id=compliance_check_id)
        
        # Only allow retry for failed or error status
        if compliance_check.status not in [ComplianceCheck.STATUS_REJECTED, ComplianceCheck.STATUS_ERROR]:
            return JsonResponse({"error": "Can only retry failed checks"}, status=400)
        
        # Reset status and retry
        compliance_check.status = ComplianceCheck.STATUS_PENDING
        compliance_check.rejection_reason = ""
        compliance_check.save()
        
        # Use real AI service if configured, otherwise fall back to mock
        try:
            ai_service = ComplianceAIService()
            updated_check = ai_service.check_compliance(compliance_check.evidence.id)
        except Exception as e:
            # Fall back to mock service if AI is not configured
            ai_service = MockAIService()
            updated_check = ai_service.check_compliance(compliance_check.evidence.id)
        
        return JsonResponse({
            "compliance_check_id": updated_check.id,
            "status": updated_check.status,
            "ai_analysis": updated_check.ai_analysis,
            "rejection_reason": updated_check.rejection_reason,
            "recommendations": updated_check.recommendations
        })
        
    except ComplianceCheck.DoesNotExist:
        return JsonResponse({"error": "Compliance check not found"}, status=404)
    except Exception as e:
        logger.error(f"Retry compliance check failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def get_ai_status(request):
    """Get AI service status"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication credentials were not provided."}, status=403)
    
    try:
        from django.conf import settings
        
        ai_url = getattr(settings, 'AI_API_URL', None)
        ai_key = getattr(settings, 'AI_API_KEY', None)
        ai_model = getattr(settings, 'AI_MODEL', 'gpt-4-vision-preview')
        
        is_configured = bool(ai_url and ai_key)
        
        return JsonResponse({
            "is_configured": is_configured,
            "api_url": ai_url if is_configured else None,
            "model": ai_model,
            "has_api_key": bool(ai_key)
        })
        
    except Exception as e:
        logger.error(f"Failed to get AI status: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)