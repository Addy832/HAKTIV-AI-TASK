from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Control, Evidence
from .serializers import ControlSerializer, EvidenceSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    return Response({"message": "pong"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user(request):
    return Response({
        "id": request.user.id,
        "email": request.user.email,
        "role": request.user.role,
        "company": request.user.company.name if request.user.company else None
    })


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["POST"])
@csrf_exempt
def logout_view(request):
    """
    Logout view that clears Django session and returns Microsoft logout URL
    """
    # Clear Django session
    logout(request)
    
    # Return Microsoft logout URL for frontend to redirect to
    microsoft_logout_url = "https://login.microsoftonline.com/common/oauth2/v2.0/logout"
    post_logout_redirect_uri = "http://localhost:3000/login/"
    
    logout_url = f"{microsoft_logout_url}?post_logout_redirect_uri={post_logout_redirect_uri}"
    
    return JsonResponse({
        "message": "Logout successful",
        "logout_url": logout_url
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_controls(request):
    qs = Control.objects.alive().filter(company=request.user.company)
    serializer = ControlSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"]) 
@permission_classes([IsAuthenticated])
def list_evidence(request):
    qs = Evidence.objects.alive().filter(company=request.user.company)
    serializer = EvidenceSerializer(qs, many=True)
    return Response(serializer.data)


@require_http_methods(["DELETE"])
@csrf_exempt
def delete_evidence(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=403)
    
    try:
        data = json.loads(request.body)
        ids = data if isinstance(data, list) else data.get("ids", [])
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)
    
    if not ids:
        return JsonResponse({"detail": "No evidence IDs provided"}, status=400)
    
    # Soft delete evidence (only from user's company)
    delete_result = Evidence.objects.alive().filter(company=request.user.company, id__in=ids).delete()
    
    # Handle both tuple and integer return values
    if isinstance(delete_result, tuple):
        deleted_count, _ = delete_result
    else:
        deleted_count = delete_result
    
    return JsonResponse({"message": f"Deleted {deleted_count} evidence records"}, status=200)


@require_http_methods(["POST"])
@csrf_exempt
def upload_evidence(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=403)
    
    try:
        # Get file and form data
        file = request.FILES.get('file')
        control_id = request.POST.get('control')
        name = request.POST.get('name')
        
        if not file or not control_id or not name:
            return JsonResponse({"detail": "Missing required fields: file, control, name"}, status=400)
        
        # Get the control
        try:
            control = Control.objects.alive().get(id=control_id, company=request.user.company)
        except Control.DoesNotExist:
            return JsonResponse({"detail": "Control not found"}, status=404)
        
        # Create evidence
        evidence = Evidence.objects.create(
            name=name,
            file=file,
            control=control,
            company=request.user.company,
            created_by=request.user,
            status=Evidence.STATUS_REJECTED  # Default status, will be updated by AI analysis
        )
        
        # Perform AI-based compliance validation
        try:
            from compliance.services import analyze_evidence_compliance
            from compliance.models import ComplianceCheck
            
            # Create a compliance check record first
            compliance_check, created = ComplianceCheck.objects.get_or_create(
                evidence=evidence,
                defaults={'status': ComplianceCheck.STATUS_PROCESSING}
            )
            
            # Analyze the evidence for compliance
            analysis_result = analyze_evidence_compliance(
                evidence_file=evidence.file,
                control_name=control.name,
                company_name=request.user.company.name
            )
            
            # Update compliance check with results
            if analysis_result.get('is_compliant', False):
                evidence.status = Evidence.STATUS_APPROVED
                evidence.rejection_reason = None
                compliance_check.status = ComplianceCheck.STATUS_APPROVED
                compliance_check.ai_analysis = analysis_result.get('analysis', {})
            else:
                evidence.status = Evidence.STATUS_REJECTED
                evidence.rejection_reason = analysis_result.get('reason', 'Compliance check failed')
                compliance_check.status = ComplianceCheck.STATUS_REJECTED
                compliance_check.rejection_reason = analysis_result.get('reason', 'Compliance check failed')
                compliance_check.ai_analysis = analysis_result.get('analysis', {})
            
            evidence.save()
            compliance_check.save()
            
        except Exception as e:
            # Log AI analysis error but don't fail the upload
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to analyze evidence {evidence.id} with AI: {str(e)}")
            
            # Create a compliance check with error status
            try:
                from compliance.models import ComplianceCheck
                compliance_check, created = ComplianceCheck.objects.get_or_create(
                    evidence=evidence,
                    defaults={'status': ComplianceCheck.STATUS_ERROR}
                )
                compliance_check.status = ComplianceCheck.STATUS_ERROR
                compliance_check.rejection_reason = f"AI analysis failed: {str(e)}"
                compliance_check.save()
            except:
                pass  # Don't fail the upload if compliance check creation fails
        
        return JsonResponse({
            "id": evidence.id,
            "name": evidence.name,
            "file": evidence.file.url if evidence.file else None,
            "control": evidence.control.id,
            "status": evidence.status,
            "created_at": evidence.created_at.isoformat()
        }, status=201)
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Upload failed: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({"detail": f"Upload failed: {str(e)}"}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_control_status(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=403)
    
    try:
        data = json.loads(request.body)
        control_id = data.get("id")
        new_status = data.get("status")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)
    
    if new_status not in dict(Control.STATUS_CHOICES):
        return JsonResponse({"detail": "Invalid status"}, status=400)
    
    try:
        control = Control.objects.alive().get(id=control_id, company=request.user.company)
    except Control.DoesNotExist:
        return JsonResponse({"detail": "Not found"}, status=404)
    
    control.status = new_status
    control.save(update_fields=["status"])
    
    return JsonResponse(ControlSerializer(control).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rag_webhook(request):
    """
    Simple n8n webhook: expects payload with keys:
    - evidence_id: int
    - status: "approved" | "rejected"
    - reason: optional string when rejected
    If approved, also mark related control as implemented.
    """
    evidence_id = request.data.get("evidence_id")
    new_status = request.data.get("status")
    if new_status not in dict(Evidence.STATUS_CHOICES):
        return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        evidence = Evidence.objects.alive().select_related("control").get(
            id=evidence_id, company=request.user.company
        )
    except Evidence.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    evidence.status = new_status
    evidence.save(update_fields=["status"])

    if new_status == Evidence.STATUS_APPROVED:
        control = evidence.control
        control.status = Control.STATUS_IMPLEMENTED
        control.save(update_fields=["status"])

    return Response({
        "evidence_id": evidence.id,
        "evidence_status": evidence.status,
        "control_status": evidence.control.status,
        "reason": request.data.get("reason", "")
    })


