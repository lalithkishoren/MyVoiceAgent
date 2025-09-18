from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import logging

from gmail_service import get_gmail_service, EmailMessage, EmailAttachment
from voice_email_handler import get_voice_email_handler

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/gmail", tags=["gmail"])

# Pydantic models for request/response
class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    cc: Optional[EmailStr] = None
    bcc: Optional[EmailStr] = None
    is_html: bool = False

class VoiceEmailRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class NotificationEmailRequest(BaseModel):
    to: EmailStr
    event_type: str
    details: Dict[str, Any]

class EmailResponse(BaseModel):
    success: bool
    message: str
    message_id: Optional[str] = None
    error: Optional[str] = None

class VoiceEmailResponse(BaseModel):
    action: str
    message: Optional[str]
    requires_response: bool
    missing_info: Optional[List[str]] = None
    current_info: Optional[Dict[str, Any]] = None
    email_id: Optional[str] = None

@router.get("/health")
async def gmail_health_check():
    """Check Gmail service health and authentication status"""
    try:
        gmail_service = get_gmail_service()
        profile = gmail_service.get_user_profile()

        if profile['success']:
            return {
                "status": "healthy",
                "authenticated": True,
                "user_email": profile['email'],
                "service": "Gmail API v1"
            }
        else:
            return {
                "status": "unhealthy",
                "authenticated": False,
                "error": profile['error']
            }
    except Exception as e:
        logger.error(f"Gmail health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "authenticated": False,
            "error": str(e)
        }

@router.post("/send", response_model=EmailResponse)
async def send_email(request: SendEmailRequest):
    """Send an email via Gmail API"""
    try:
        gmail_service = get_gmail_service()

        result = gmail_service.send_email_with_cc_bcc(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            is_html=request.is_html
        )

        if result['success']:
            return EmailResponse(
                success=True,
                message=f"Email sent successfully to {request.to}",
                message_id=result['message_id']
            )
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/send-simple")
async def send_simple_email_get(to: EmailStr, subject: str, body: str, is_html: bool = False):
    """Send a simple email via GET (for testing)"""
    try:
        gmail_service = get_gmail_service()
        result = gmail_service.send_simple_email(to, subject, body, is_html)

        if result['success']:
            return {
                "success": True,
                "message": f"Email sent to {to}",
                "message_id": result['message_id']
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except Exception as e:
        logger.error(f"Failed to send simple email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-simple")
async def send_simple_email(to: EmailStr, subject: str, body: str, is_html: bool = False):
    """Send a simple email (alternative endpoint for quick sends)"""
    try:
        gmail_service = get_gmail_service()
        result = gmail_service.send_simple_email(to, subject, body, is_html)

        if result['success']:
            return {
                "success": True,
                "message": f"Email sent to {to}",
                "message_id": result['message_id']
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except Exception as e:
        logger.error(f"Failed to send simple email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-email", response_model=VoiceEmailResponse)
async def process_voice_email_command(request: VoiceEmailRequest):
    """Process voice commands for email functionality"""
    try:
        voice_handler = get_voice_email_handler()
        result = voice_handler.process_voice_command(request.text, request.session_id)

        return VoiceEmailResponse(**result)

    except Exception as e:
        logger.error(f"Failed to process voice email command: {str(e)}")
        return VoiceEmailResponse(
            action="error",
            message=f"Failed to process voice command: {str(e)}",
            requires_response=True
        )

@router.post("/send-notification", response_model=EmailResponse)
async def send_notification_email(request: NotificationEmailRequest, background_tasks: BackgroundTasks):
    """Send notification email (can be processed in background)"""
    try:
        voice_handler = get_voice_email_handler()

        # Send notification in background to avoid blocking
        def send_notification():
            result = voice_handler.send_notification_email(
                to=request.to,
                event_type=request.event_type,
                details=request.details
            )
            if result['success']:
                logger.info(f"Notification email sent to {request.to}")
            else:
                logger.error(f"Failed to send notification email: {result['error']}")

        background_tasks.add_task(send_notification)

        return EmailResponse(
            success=True,
            message=f"Notification email queued for sending to {request.to}"
        )

    except Exception as e:
        logger.error(f"Failed to queue notification email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_gmail_profile():
    """Get Gmail user profile information"""
    try:
        gmail_service = get_gmail_service()
        profile = gmail_service.get_user_profile()

        if profile['success']:
            return profile
        else:
            raise HTTPException(status_code=400, detail=profile['error'])

    except Exception as e:
        logger.error(f"Failed to get Gmail profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/email-context/{session_id}")
async def clear_email_context(session_id: str):
    """Clear email context for a specific session"""
    try:
        voice_handler = get_voice_email_handler()

        if session_id in voice_handler.email_context:
            del voice_handler.email_context[session_id]
            return {"success": True, "message": f"Email context cleared for session {session_id}"}
        else:
            return {"success": False, "message": f"No email context found for session {session_id}"}

    except Exception as e:
        logger.error(f"Failed to clear email context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup-contexts")
async def cleanup_old_email_contexts(max_age_minutes: int = 30):
    """Clean up old email contexts"""
    try:
        voice_handler = get_voice_email_handler()
        voice_handler.cleanup_old_contexts(max_age_minutes)

        return {
            "success": True,
            "message": f"Email contexts older than {max_age_minutes} minutes have been cleaned up"
        }

    except Exception as e:
        logger.error(f"Failed to cleanup email contexts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility endpoint for testing
@router.post("/test-email-extraction")
async def test_email_extraction(text: str):
    """Test email component extraction from voice text"""
    try:
        voice_handler = get_voice_email_handler()
        components = voice_handler.extract_email_components(text)

        return {
            "input_text": text,
            "extracted_components": components
        }

    except Exception as e:
        logger.error(f"Failed to test email extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))