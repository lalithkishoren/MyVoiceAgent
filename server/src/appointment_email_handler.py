import re
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from gmail_service import get_gmail_service

logger = logging.getLogger(__name__)

class AppointmentEmailHandler:
    """Handles automatic appointment confirmation email sending"""

    def __init__(self):
        self.gmail_service = None
        try:
            self.gmail_service = get_gmail_service()
            logger.info("Appointment email handler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize appointment email handler: {str(e)}")

    def extract_email_confirmation_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract email confirmation data from AI response text"""
        try:
            # Look for SEND_EMAIL pattern: SEND_EMAIL: recipient_email|patient_name|appointment_date|doctor_name|department_name|phone_number
            pattern = r'SEND_EMAIL:\s*([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)

            if not match:
                return None

            # Extract the pipe-separated values
            try:
                data = {
                    'recipient': match.group(1).strip(),
                    'patient_name': match.group(2).strip(),
                    'appointment_date': match.group(3).strip(),
                    'doctor_name': match.group(4).strip(),
                    'department': match.group(5).strip(),
                    'phone': match.group(6).strip()
                }
                logger.info(f"Extracted appointment confirmation data: {data}")
                return data
            except Exception as e:
                logger.error(f"Error parsing SEND_EMAIL data: {e}")
                return None

        except Exception as e:
            logger.error(f"Error extracting email confirmation data: {str(e)}")
            return None

    def _manual_parse_confirmation_data(self, content: str) -> Dict[str, Any]:
        """Manually parse confirmation data when JSON parsing fails"""
        data = {}

        # Extract key-value pairs
        patterns = {
            'recipient': r'"recipient":\s*"([^"]+)"',
            'patient_name': r'"patient_name":\s*"([^"]+)"',
            'appointment_date': r'"appointment_date":\s*"([^"]+)"',
            'doctor_name': r'"doctor_name":\s*"([^"]+)"',
            'department': r'"department":\s*"([^"]+)"',
            'phone': r'"phone":\s*"([^"]+)"'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data[key] = match.group(1)

        return data

    def send_appointment_confirmation(self, confirmation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send appointment confirmation email"""
        try:
            if not self.gmail_service:
                return {
                    'success': False,
                    'error': 'Gmail service not available'
                }

            # Validate required fields
            required_fields = ['recipient', 'patient_name', 'appointment_date', 'doctor_name', 'department']
            missing_fields = [field for field in required_fields if not confirmation_data.get(field)]

            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }

            # Generate email content
            subject = f"Appointment Confirmed - {confirmation_data.get('appointment_date')} - Renova Hospitals"

            html_body = self._generate_confirmation_email_html(confirmation_data)

            # Send email
            result = self.gmail_service.send_simple_email(
                to=confirmation_data['recipient'],
                subject=subject,
                body=html_body,
                is_html=True
            )

            if result['success']:
                logger.info(f"Appointment confirmation email sent to {confirmation_data['recipient']}")
                return {
                    'success': True,
                    'message': f"Confirmation email sent to {confirmation_data['recipient']}",
                    'email_id': result.get('message_id')
                }
            else:
                logger.error(f"Failed to send appointment confirmation: {result['error']}")
                return {
                    'success': False,
                    'error': result['error']
                }

        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_confirmation_email_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML email content for appointment confirmation"""

        # Format phone number nicely
        phone = data.get('phone', 'Not provided')
        if phone and not phone.startswith('+'):
            phone = f"+91-{phone}" if phone.startswith(('6', '7', '8', '9')) else phone

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Confirmation - Renova Hospitals</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

                <!-- Header -->
                <div style="background: linear-gradient(135deg, #2c5aa0 0%, #1e3d72 100%); color: white; padding: 30px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 300;">🏥 Renova Hospitals</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your Appointment is Confirmed</p>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #2c5aa0; margin-top: 0; margin-bottom: 20px;">Dear {data.get('patient_name', 'Patient')},</h2>

                    <p style="color: #555; line-height: 1.6; margin-bottom: 25px;">
                        Thank you for scheduling your appointment with us. Your appointment has been confirmed with the following details:
                    </p>

                    <!-- Appointment Details Card -->
                    <div style="background-color: #f8fafc; border-left: 4px solid #2c5aa0; padding: 25px; margin: 25px 0; border-radius: 5px;">
                        <h3 style="color: #2c5aa0; margin-top: 0; margin-bottom: 15px;">📅 Appointment Details</h3>

                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #666; font-weight: 600; width: 140px;">Date & Time:</td>
                                <td style="padding: 8px 0; color: #333;">{data.get('appointment_date', 'Not specified')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666; font-weight: 600;">Doctor:</td>
                                <td style="padding: 8px 0; color: #333;">{data.get('doctor_name', 'Not specified')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666; font-weight: 600;">Department:</td>
                                <td style="padding: 8px 0; color: #333;">{data.get('department', 'Not specified')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666; font-weight: 600;">Patient:</td>
                                <td style="padding: 8px 0; color: #333;">{data.get('patient_name', 'Not specified')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666; font-weight: 600;">Phone:</td>
                                <td style="padding: 8px 0; color: #333;">{phone}</td>
                            </tr>
                        </table>
                    </div>

                    <!-- Important Instructions -->
                    <div style="background-color: #fff8e1; border: 1px solid #ffd54f; padding: 20px; border-radius: 5px; margin: 25px 0;">
                        <h3 style="color: #f57c00; margin-top: 0; margin-bottom: 15px;">⚠️ Important Instructions</h3>
                        <ul style="color: #666; line-height: 1.6; margin: 0; padding-left: 20px;">
                            <li>Please arrive <strong>15 minutes early</strong> for check-in</li>
                            <li>Bring a valid <strong>photo ID</strong> and <strong>insurance card</strong></li>
                            <li>Bring a list of your <strong>current medications</strong></li>
                            <li>Wear comfortable, loose-fitting clothing if applicable</li>
                            <li>Fast for 8-12 hours if lab work is required (if instructed)</li>
                        </ul>
                    </div>

                    <!-- Hospital Information -->
                    <div style="border-top: 1px solid #e0e0e0; padding-top: 25px; margin-top: 30px;">
                        <h3 style="color: #2c5aa0; margin-top: 0; margin-bottom: 15px;">🏥 Hospital Information</h3>
                        <p style="color: #666; line-height: 1.6; margin: 0;">
                            <strong>Renova Hospitals</strong><br>
                            123 Healthcare Avenue, Medical District<br>
                            City, State - 123456<br>
                            <strong>Phone:</strong> +91-11-1234-5678<br>
                            <strong>Emergency:</strong> +91-11-1234-9999
                        </p>
                    </div>

                    <!-- Rescheduling Information -->
                    <div style="background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin: 25px 0;">
                        <h3 style="color: #1976d2; margin-top: 0; margin-bottom: 10px;">📞 Need to Reschedule?</h3>
                        <p style="color: #666; line-height: 1.6; margin: 0;">
                            If you need to reschedule or cancel your appointment, please call us at least
                            <strong>24 hours in advance</strong> at +91-11-1234-5678 or speak with Archana,
                            our AI assistant, at any time.
                        </p>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #f5f5f5; padding: 25px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                    <p style="color: #888; font-size: 14px; margin: 0; line-height: 1.5;">
                        This appointment confirmation was generated by <strong>Archana</strong>,
                        your AI Assistant at Renova Hospitals.<br>
                        <em>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em>
                    </p>

                    <div style="margin-top: 15px;">
                        <p style="color: #2c5aa0; font-weight: 600; margin: 0; font-size: 16px;">
                            🌟 Thank you for choosing Renova Hospitals
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def process_ai_response(self, ai_response: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Process AI response and send appointment confirmation email if needed

        Returns:
            tuple: (cleaned_response, email_result)
        """
        try:
            # Extract confirmation data from response
            confirmation_data = self.extract_email_confirmation_data(ai_response)

            if not confirmation_data:
                return ai_response, None

            # Send the confirmation email
            result = self.send_appointment_confirmation(confirmation_data)

            if result['success']:
                logger.info(f"Successfully processed appointment confirmation for {confirmation_data.get('patient_name')}")
            else:
                logger.error(f"Failed to send appointment confirmation: {result['error']}")

            # Remove the SEND_EMAIL trigger from the response
            pattern = r'SEND_EMAIL:\s*([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|\n]+)'
            cleaned_response = re.sub(pattern, '', ai_response, flags=re.IGNORECASE).strip()

            return cleaned_response, result

        except Exception as e:
            logger.error(f"Error processing AI response for appointment confirmation: {str(e)}")
            return ai_response, {
                'success': False,
                'error': str(e)
            }

# Global appointment email handler
_appointment_email_handler = None

def get_appointment_email_handler() -> AppointmentEmailHandler:
    """Get singleton appointment email handler"""
    global _appointment_email_handler
    if _appointment_email_handler is None:
        _appointment_email_handler = AppointmentEmailHandler()
    return _appointment_email_handler