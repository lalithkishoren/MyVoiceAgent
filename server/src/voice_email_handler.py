import json
import logging
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from gmail_service import get_gmail_service, EmailMessage

logger = logging.getLogger(__name__)

class VoiceEmailHandler:
    """Handles email-related voice commands and sends emails via Gmail API"""

    def __init__(self):
        self.gmail_service = get_gmail_service()
        self.email_context = {}  # Store ongoing email composition context

    def extract_email_components(self, text: str) -> Dict[str, Any]:
        """Extract email components from voice text using pattern matching"""

        # Common patterns for email extraction
        patterns = {
            'email_addresses': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            'send_email_trigger': r'\b(?:send|write|compose|email)\s+(?:an?\s+)?email\b',
            'subject_pattern': r'\b(?:subject|title|regarding|about)(?:\s+is)?\s*[:\-]?\s*(.+?)(?:\s+(?:body|message|content|text)|$)',
            'recipient_pattern': r'\b(?:to|send\s+to|email\s+to|recipient)\s*[:\-]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'body_pattern': r'\b(?:body|message|content|text|saying|write)(?:\s+is)?\s*[:\-]?\s*(.+)',
        }

        result = {
            'has_email_intent': False,
            'recipient': None,
            'subject': None,
            'body': None,
            'emails_found': []
        }

        # Check for email intent
        if re.search(patterns['send_email_trigger'], text, re.IGNORECASE):
            result['has_email_intent'] = True

        # Find email addresses
        email_matches = re.findall(patterns['email_addresses'], text, re.IGNORECASE)
        result['emails_found'] = email_matches

        if email_matches:
            result['recipient'] = email_matches[0]  # Use first email as recipient

        # Extract subject
        subject_match = re.search(patterns['subject_pattern'], text, re.IGNORECASE)
        if subject_match:
            result['subject'] = subject_match.group(1).strip()

        # Extract recipient if not found in general email search
        if not result['recipient']:
            recipient_match = re.search(patterns['recipient_pattern'], text, re.IGNORECASE)
            if recipient_match:
                result['recipient'] = recipient_match.group(1).strip()

        # Extract body
        body_match = re.search(patterns['body_pattern'], text, re.IGNORECASE)
        if body_match:
            result['body'] = body_match.group(1).strip()

        return result

    def process_voice_command(self, text: str, session_id: str = None) -> Dict[str, Any]:
        """Process voice command for email-related actions"""
        try:
            # Extract email components from voice text
            components = self.extract_email_components(text)

            if not components['has_email_intent']:
                return {
                    'action': 'none',
                    'message': None,
                    'requires_response': False
                }

            # Check if this is a complete email request
            if components['recipient'] and components['subject'] and components['body']:
                return self._send_complete_email(components)

            # Handle partial email requests - start conversation to collect missing info
            return self._handle_partial_email_request(components, session_id, text)

        except Exception as e:
            logger.error(f"Error processing voice email command: {str(e)}")
            return {
                'action': 'error',
                'message': f"Sorry, I encountered an error while processing your email request: {str(e)}",
                'requires_response': True
            }

    def _send_complete_email(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Send email when all components are available"""
        try:
            result = self.gmail_service.send_simple_email(
                to=components['recipient'],
                subject=components['subject'],
                body=components['body']
            )

            if result['success']:
                return {
                    'action': 'email_sent',
                    'message': f"Email sent successfully to {components['recipient']} with subject '{components['subject']}'",
                    'requires_response': True,
                    'email_id': result['message_id']
                }
            else:
                return {
                    'action': 'email_failed',
                    'message': f"Failed to send email: {result['error']}",
                    'requires_response': True
                }

        except Exception as e:
            logger.error(f"Error sending complete email: {str(e)}")
            return {
                'action': 'error',
                'message': f"Failed to send email: {str(e)}",
                'requires_response': True
            }

    def _handle_partial_email_request(self, components: Dict[str, Any], session_id: str, original_text: str) -> Dict[str, Any]:
        """Handle partial email requests by asking for missing information"""

        # Store context for this session
        if session_id:
            if session_id not in self.email_context:
                self.email_context[session_id] = {}

            context = self.email_context[session_id]

            # Update context with new information
            if components['recipient']:
                context['recipient'] = components['recipient']
            if components['subject']:
                context['subject'] = components['subject']
            if components['body']:
                context['body'] = components['body']

            context['last_interaction'] = datetime.now()

        # Determine what information is missing
        missing_info = []
        current_info = components

        if session_id and session_id in self.email_context:
            # Merge with stored context
            stored_context = self.email_context[session_id]
            current_info = {
                'recipient': current_info.get('recipient') or stored_context.get('recipient'),
                'subject': current_info.get('subject') or stored_context.get('subject'),
                'body': current_info.get('body') or stored_context.get('body')
            }

        if not current_info['recipient']:
            missing_info.append('recipient email address')
        if not current_info['subject']:
            missing_info.append('subject')
        if not current_info['body']:
            missing_info.append('message content')

        if not missing_info:
            # All info collected, send the email
            return self._send_complete_email(current_info)

        # Ask for missing information
        if len(missing_info) == 3:
            message = "I'd be happy to help you send an email. Could you please provide the recipient's email address, subject, and message content?"
        elif len(missing_info) == 2:
            message = f"I need a bit more information. Please provide the {' and '.join(missing_info)}."
        else:
            message = f"I just need the {missing_info[0]} to send your email."

        return {
            'action': 'collect_email_info',
            'message': message,
            'requires_response': True,
            'missing_info': missing_info,
            'current_info': current_info
        }

    def send_notification_email(self, to: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification emails for various events (call summaries, alerts, etc.)"""

        try:
            # Generate email content based on event type
            subject, body = self._generate_notification_content(event_type, details)

            result = self.gmail_service.send_simple_email(
                to=to,
                subject=subject,
                body=body,
                is_html=True
            )

            if result['success']:
                logger.info(f"Notification email sent to {to} for {event_type}")
            else:
                logger.error(f"Failed to send notification email: {result['error']}")

            return result

        except Exception as e:
            logger.error(f"Error sending notification email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_notification_content(self, event_type: str, details: Dict[str, Any]) -> Tuple[str, str]:
        """Generate email subject and body for different notification types"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if event_type == 'call_summary':
            subject = f"Call Summary - {details.get('caller', 'Unknown')} - {timestamp}"
            body = f"""
            <html>
            <body>
            <h2>Voice Call Summary</h2>
            <p><strong>Date/Time:</strong> {timestamp}</p>
            <p><strong>Caller:</strong> {details.get('caller', 'Unknown')}</p>
            <p><strong>Duration:</strong> {details.get('duration', 'Unknown')}</p>
            <p><strong>Summary:</strong></p>
            <p>{details.get('summary', 'No summary available')}</p>
            <hr>
            <p><em>Generated by Renova Hospitals AI Voice Agent</em></p>
            </body>
            </html>
            """

        elif event_type == 'appointment_request':
            subject = f"New Appointment Request - {details.get('patient_name', 'Unknown')} - {timestamp}"
            body = f"""
            <html>
            <body>
            <h2>New Appointment Request</h2>
            <p><strong>Patient Name:</strong> {details.get('patient_name', 'Not provided')}</p>
            <p><strong>Phone:</strong> {details.get('phone', 'Not provided')}</p>
            <p><strong>Preferred Date:</strong> {details.get('preferred_date', 'Not specified')}</p>
            <p><strong>Reason:</strong> {details.get('reason', 'Not specified')}</p>
            <p><strong>Notes:</strong> {details.get('notes', 'None')}</p>
            <hr>
            <p><em>Generated by Renova Hospitals AI Voice Agent</em></p>
            </body>
            </html>
            """

        else:
            subject = f"Voice Agent Notification - {event_type} - {timestamp}"
            body = f"""
            <html>
            <body>
            <h2>Voice Agent Notification</h2>
            <p><strong>Event Type:</strong> {event_type}</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>Details:</strong></p>
            <pre>{json.dumps(details, indent=2)}</pre>
            <hr>
            <p><em>Generated by Renova Hospitals AI Voice Agent</em></p>
            </body>
            </html>
            """

        return subject, body

    def cleanup_old_contexts(self, max_age_minutes: int = 30):
        """Clean up old email contexts to prevent memory leaks"""
        try:
            current_time = datetime.now()
            sessions_to_remove = []

            for session_id, context in self.email_context.items():
                if 'last_interaction' in context:
                    age_minutes = (current_time - context['last_interaction']).total_seconds() / 60
                    if age_minutes > max_age_minutes:
                        sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.email_context[session_id]
                logger.info(f"Cleaned up old email context for session {session_id}")

        except Exception as e:
            logger.error(f"Error cleaning up email contexts: {str(e)}")

# Global voice email handler instance
_voice_email_handler = None

def get_voice_email_handler() -> VoiceEmailHandler:
    """Get singleton voice email handler instance"""
    global _voice_email_handler
    if _voice_email_handler is None:
        _voice_email_handler = VoiceEmailHandler()
    return _voice_email_handler