import requests
import json
import base64
from typing import Dict, Any, Optional
from django.conf import settings
from .models import ComplianceCheck


class ComplianceAIService:
    """Service for AI-powered compliance checking"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'AI_API_URL', None)
        self.api_key = getattr(settings, 'AI_API_KEY', None)
        self.model = getattr(settings, 'AI_MODEL', 'gpt-4-vision-preview')
    
    def _is_configured(self) -> bool:
        """Check if AI service is properly configured"""
        return bool(self.api_url and self.api_key)
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to encode image: {str(e)}")
    
    def _call_ai_api(self, image_base64: str, control_type: str) -> Dict[str, Any]:
        """Call the Gemini API for compliance checking"""
        if not self._is_configured():
            raise Exception("AI service not configured. Please set AI_API_URL and AI_API_KEY in environment variables.")
        
        # Prepare the prompt based on control type
        if control_type == "MFA":
            prompt = "Analyze this image for MFA (Multi-Factor Authentication) compliance. Look for: OTP, One-Time Password, TOTP, Authenticator, numeric input fields, QR codes, 6-digit codes, security keys. Return JSON: {\"is_compliant\": boolean, \"confidence\": float, \"detected_elements\": [list], \"reasoning\": \"explanation\"}"
        elif control_type == "SSO":
            prompt = "Analyze this image for SSO (Single Sign-On) compliance with Microsoft. Look for: Microsoft branding, 'Sign in with Microsoft', 'Microsoft Account', 'Azure AD', Office 365, Microsoft 365. Return JSON: {\"is_compliant\": boolean, \"confidence\": float, \"detected_elements\": [list], \"reasoning\": \"explanation\"}"
        else:
            raise Exception(f"Unknown control type: {control_type}")
        
        # Prepare the API request for Gemini
        headers = {
            'X-goog-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Gemini API format
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': prompt
                        },
                        {
                            'inline_data': {
                                'mime_type': 'image/jpeg',
                                'data': image_base64
                            }
                        }
                    ]
                }
            ],
            'generationConfig': {
                'maxOutputTokens': 500,
                'temperature': 0.1
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Parse Gemini response
            result = response.json()
            
            # Extract text from Gemini response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text_response = candidate['content']['parts'][0]['text']
                else:
                    raise Exception("No content in Gemini response")
            else:
                raise Exception("No response from Gemini API")
            
            # Try to parse JSON from the response
            try:
                import re
                json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group())
                    return parsed_json
                else:
                    # Fallback: create response from text analysis
                    return self._parse_text_response(text_response, control_type)
            except json.JSONDecodeError:
                # Fallback: create response from text analysis
                return self._parse_text_response(text_response, control_type)
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gemini API request failed: {str(e)}")
    
    def _parse_text_response(self, text: str, control_type: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        text_lower = text.lower()
        
        if control_type == "MFA":
            mfa_keywords = ['otp', 'one-time password', 'totp', 'authenticator', '6-digit', 'qr code']
            found_elements = [kw for kw in mfa_keywords if kw in text_lower]
            is_compliant = len(found_elements) > 0
        else:  # SSO
            sso_keywords = ['microsoft', 'azure', 'office 365', 'sign in with microsoft', 'microsoft account']
            found_elements = [kw for kw in sso_keywords if kw in text_lower]
            is_compliant = len(found_elements) > 0
        
        return {
            'is_compliant': is_compliant,
            'confidence': 0.7 if is_compliant else 0.3,
            'detected_elements': found_elements,
            'reasoning': f"AI analysis: {text[:200]}..."
        }
    
    def check_compliance(self, evidence_id: int) -> ComplianceCheck:
        """Check compliance for a specific evidence item"""
        try:
            from api.models import Evidence
            evidence = Evidence.objects.get(id=evidence_id)
        except Evidence.DoesNotExist:
            raise Exception(f"Evidence with ID {evidence_id} not found")
        
        # Create or get compliance check
        compliance_check, created = ComplianceCheck.objects.get_or_create(
            evidence=evidence,
            defaults={'status': ComplianceCheck.STATUS_PENDING}
        )
        
        if compliance_check.status == ComplianceCheck.STATUS_PROCESSING:
            raise Exception("Compliance check already in progress")
        
        # Update status to processing
        compliance_check.status = ComplianceCheck.STATUS_PROCESSING
        compliance_check.save()
        
        try:
            # Get the control type from the evidence's control
            control_type = self._get_control_type(evidence.control)
            
            # Encode the image
            if not evidence.file:
                raise Exception("No file attached to evidence")
            
            image_base64 = self._encode_image(evidence.file.path)
            
            # Call AI API
            ai_response = self._call_ai_api(image_base64, control_type)
            
            # Process the response
            compliance_check.ai_analysis = ai_response
            compliance_check.status = ComplianceCheck.STATUS_APPROVED if ai_response.get('is_compliant') else ComplianceCheck.STATUS_REJECTED
            
            if not ai_response.get('is_compliant'):
                compliance_check.rejection_reason = ai_response.get('reasoning', 'Compliance check failed')
            
            compliance_check.recommendations = self._generate_recommendations(ai_response, control_type)
            
            # Update evidence and control status
            if compliance_check.status == ComplianceCheck.STATUS_APPROVED:
                evidence.status = Evidence.STATUS_APPROVED
                evidence.save()
                
                # Update control status to implemented
                evidence.control.status = Control.STATUS_IMPLEMENTED
                evidence.control.save()
            
        except Exception as e:
            compliance_check.status = ComplianceCheck.STATUS_ERROR
            compliance_check.rejection_reason = str(e)
        
        compliance_check.save()
        return compliance_check
    
    def _get_control_type(self, control) -> str:
        """Determine control type from control name or other attributes"""
        control_name = control.name.lower()
        
        if any(keyword in control_name for keyword in ['mfa', 'multi-factor', 'otp', 'authenticator']):
            return "MFA"
        elif any(keyword in control_name for keyword in ['sso', 'single sign-on', 'microsoft', 'azure']):
            return "SSO"
        else:
            # Default to MFA if unclear
            return "MFA"
    
    def _generate_recommendations(self, ai_response: Dict[str, Any], control_type: str) -> str:
        """Generate recommendations based on AI analysis"""
        recommendations = []
        
        if not ai_response.get('is_compliant'):
            if control_type == "MFA":
                recommendations.extend([
                    "Ensure OTP input field is clearly visible",
                    "Add clear labeling for 'One-Time Password' or 'OTP'",
                    "Include instructions for using authenticator apps",
                    "Consider adding QR code for easy setup"
                ])
            elif control_type == "SSO":
                recommendations.extend([
                    "Add Microsoft branding and logos",
                    "Include 'Sign in with Microsoft' button",
                    "Ensure Azure AD integration is visible",
                    "Add clear SSO login instructions"
                ])
        
        return "\n".join(recommendations) if recommendations else "No specific recommendations at this time."


class MockAIService:
    """Mock AI service for testing without actual API calls"""
    
    def check_compliance(self, evidence_id: int) -> ComplianceCheck:
        """Mock compliance check for testing"""
        try:
            from api.models import Evidence
            evidence = Evidence.objects.get(id=evidence_id)
        except Evidence.DoesNotExist:
            raise Exception(f"Evidence with ID {evidence_id} not found")
        
        # Create or get compliance check
        compliance_check, created = ComplianceCheck.objects.get_or_create(
            evidence=evidence,
            defaults={'status': ComplianceCheck.STATUS_PENDING}
        )
        
        compliance_check.status = ComplianceCheck.STATUS_PROCESSING
        compliance_check.save()
        
        # Mock AI analysis
        control_type = self._get_control_type(evidence.control)
        
        if control_type == "MFA":
            mock_response = {
                "is_compliant": True,
                "confidence": 0.85,
                "detected_elements": ["OTP input field", "6-digit code format", "Authenticator app reference"],
                "reasoning": "Screenshot shows clear OTP input field with proper labeling"
            }
        else:  # SSO
            mock_response = {
                "is_compliant": True,
                "confidence": 0.90,
                "detected_elements": ["Microsoft logo", "Sign in with Microsoft button", "Azure AD branding"],
                "reasoning": "Screenshot shows Microsoft SSO integration with proper branding"
            }
        
        compliance_check.ai_analysis = mock_response
        compliance_check.status = ComplianceCheck.STATUS_APPROVED
        compliance_check.recommendations = "Mock analysis completed successfully."
        
        # Update evidence and control status
        from api.models import Control
        evidence.status = Evidence.STATUS_APPROVED
        evidence.save()
        
        evidence.control.status = Control.STATUS_IMPLEMENTED
        evidence.control.save()
        
        compliance_check.save()
        return compliance_check
    
    def _get_control_type(self, control) -> str:
        """Determine control type from control name"""
        control_name = control.name.lower()
        
        if any(keyword in control_name for keyword in ['mfa', 'multi-factor', 'otp', 'authenticator']):
            return "MFA"
        elif any(keyword in control_name for keyword in ['sso', 'single sign-on', 'microsoft', 'azure']):
            return "SSO"
        else:
            return "MFA"


def analyze_evidence_compliance(evidence_file, control_name: str, company_name: str) -> Dict[str, Any]:
    """
    Analyze evidence for compliance using AI service
    This function is called directly from the upload view
    """
    try:
        # Initialize the AI service
        ai_service = ComplianceAIService()
        
        # Determine control type from control name
        control_type = ai_service._get_control_type_from_name(control_name)
        
        # Encode the image
        if not evidence_file:
            return {
                'is_compliant': False,
                'reason': 'No file attached to evidence'
            }
        
        image_base64 = ai_service._encode_image(evidence_file.path)
        
        # Call AI API
        ai_response = ai_service._call_ai_api(image_base64, control_type)
        
        # Return the analysis result
        return {
            'is_compliant': ai_response.get('is_compliant', False),
            'reason': ai_response.get('reasoning', 'Compliance check failed'),
            'confidence': ai_response.get('confidence', 0.0),
            'detected_elements': ai_response.get('detected_elements', []),
            'analysis': ai_response
        }
        
    except Exception as e:
        # Return failure result if AI analysis fails
        return {
            'is_compliant': False,
            'reason': f'AI analysis failed: {str(e)}',
            'confidence': 0.0,
            'detected_elements': [],
            'analysis': {}
        }


# Add helper method to ComplianceAIService
def _get_control_type_from_name(self, control_name: str) -> str:
    """Determine control type from control name string"""
    control_name_lower = control_name.lower()
    
    if any(keyword in control_name_lower for keyword in ['mfa', 'multi-factor', 'otp', 'authenticator']):
        return "MFA"
    elif any(keyword in control_name_lower for keyword in ['sso', 'single sign-on', 'microsoft', 'azure']):
        return "SSO"
    else:
        # Default to MFA if unclear
        return "MFA"

# Monkey patch the method to the class
ComplianceAIService._get_control_type_from_name = _get_control_type_from_name
