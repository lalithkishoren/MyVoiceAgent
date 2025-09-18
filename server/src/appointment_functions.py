#!/usr/bin/env python3

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from gmail_service import get_gmail_service
import logging

logger = logging.getLogger(__name__)

# Define the appointment email function schema
send_appointment_email_function = FunctionSchema(
    name="send_appointment_email",
    description="Send appointment confirmation email to patient after booking is confirmed",
    properties={
        "patient_name": {
            "type": "string",
            "description": "Full name of the patient"
        },
        "email": {
            "type": "string",
            "description": "Patient's email address"
        },
        "phone": {
            "type": "string",
            "description": "Patient's phone number"
        },
        "appointment_date": {
            "type": "string",
            "description": "Date of the appointment (e.g., 2024-01-15)"
        },
        "appointment_time": {
            "type": "string",
            "description": "Time of the appointment (e.g., 10:00 AM)"
        },
        "doctor_name": {
            "type": "string",
            "description": "Name of the doctor assigned"
        },
        "department": {
            "type": "string",
            "description": "Hospital department (e.g., Cardiology, General Medicine)"
        }
    },
    required=["patient_name", "email", "appointment_date", "appointment_time", "doctor_name", "department"]
)

# Create tools schema with the appointment function
appointment_tools = ToolsSchema(standard_tools=[send_appointment_email_function])

def create_appointment_email_html(patient_name: str, email: str, phone: str,
                                appointment_date: str, appointment_time: str,
                                doctor_name: str, department: str) -> tuple[str, str]:
    """Create HTML email content for appointment confirmation"""

    # Create subject
    subject = f"Appointment Confirmed - Renova Hospitals - {appointment_date}"

    # Create HTML body
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0;">Renova Hospitals</h1>
                <p style="color: white; margin: 5px 0 0 0;">Appointment Confirmation</p>
            </div>

            <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #333; margin-top: 0;">Dear {patient_name},</h2>
                <p>Your appointment has been confirmed! We're looking forward to seeing you at Renova Hospitals.</p>
            </div>

            <div style="background: white; border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #667eea; margin-top: 0;">Appointment Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Patient Name:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{patient_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Date:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{appointment_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Time:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{appointment_time}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Doctor:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{doctor_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Department:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{department}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;"><strong>Contact Phone:</strong></td>
                        <td style="padding: 8px 0;">{phone}</td>
                    </tr>
                </table>
            </div>

            <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 20px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">Important Reminders:</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Please arrive 15 minutes before your appointment time</li>
                    <li>Bring a valid photo ID and insurance card</li>
                    <li>If you need to reschedule, please call us at least 24 hours in advance</li>
                </ul>
            </div>

            <div style="text-align: center; padding: 20px 0;">
                <p style="margin: 0;">Thank you for choosing Renova Hospitals!</p>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">
                    For any questions, please contact us at: <a href="mailto:info@renovahospitals.com" style="color: #667eea;">info@renovahospitals.com</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return subject, body

async def handle_send_appointment_email(params: FunctionCallParams):
    """Handle the send_appointment_email function call from Gemini Live - includes email AND calendar"""
    try:
        # Extract parameters from function call
        function_args = params.arguments

        patient_name = function_args.get("patient_name")
        email = function_args.get("email")
        phone = function_args.get("phone", "Not provided")
        appointment_date = function_args.get("appointment_date")
        appointment_time = function_args.get("appointment_time")
        doctor_name = function_args.get("doctor_name")
        department = function_args.get("department")

        print(f"=== FUNCTION CALL: send_appointment_email ===")
        print(f"Patient: {patient_name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print(f"Date: {appointment_date}")
        print(f"Time: {appointment_time}")
        print(f"Doctor: {doctor_name}")
        print(f"Department: {department}")

        # Validate required fields
        if not all([patient_name, email, appointment_date, appointment_time, doctor_name, department]):
            error_msg = "Missing required appointment details"
            print(f"=== [ERROR] {error_msg} ===")
            await params.result_callback({
                "success": False,
                "error": error_msg,
                "message": "Please provide all required appointment details."
            })
            return

        # Create email content
        subject, body = create_appointment_email_html(
            patient_name, email, phone, appointment_date,
            appointment_time, doctor_name, department
        )

        # 1. Send email using existing Gmail service
        gmail_service = get_gmail_service()
        email_result = gmail_service.send_simple_email(
            to=email,
            subject=subject,
            body=body,
            is_html=True
        )

        # 2. Add to Google Calendar using existing Google auth
        from calendar_service import get_calendar_service
        calendar_service = get_calendar_service()
        calendar_result = calendar_service.create_appointment_event(
            patient_name=patient_name,
            patient_email=email,
            patient_phone=phone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            doctor_name=doctor_name,
            department=department
        )

        # Evaluate results
        email_success = email_result.get('success', False)
        calendar_success = calendar_result.get('success', False)

        if email_success and calendar_success:
            success_msg = f"Appointment confirmed! Email sent to {email} and added to hospital calendar."
            print(f"=== [SUCCESS] Email + Calendar: {success_msg} ===")
            await params.result_callback({
                "success": True,
                "message": success_msg,
                "email_sent_to": email,
                "calendar_event_id": calendar_result.get('event_id'),
                "email_message_id": email_result.get('message_id'),
                "appointment_details": {
                    "patient": patient_name,
                    "date": appointment_date,
                    "time": appointment_time,
                    "doctor": doctor_name,
                    "department": department
                }
            })
        elif email_success and not calendar_success:
            partial_msg = f"Email sent to {email}, but calendar update failed: {calendar_result.get('error', 'Unknown error')}"
            print(f"=== [PARTIAL] {partial_msg} ===")
            await params.result_callback({
                "success": True,
                "message": f"Email confirmation sent to {email}. Please manually add to calendar.",
                "email_sent_to": email,
                "calendar_error": calendar_result.get('error'),
                "appointment_details": {
                    "patient": patient_name,
                    "date": appointment_date,
                    "time": appointment_time,
                    "doctor": doctor_name,
                    "department": department
                }
            })
        elif not email_success and calendar_success:
            partial_msg = f"Calendar updated but email failed: {email_result.get('error', 'Unknown error')}"
            print(f"=== [PARTIAL] {partial_msg} ===")
            await params.result_callback({
                "success": True,
                "message": f"Appointment added to hospital calendar. Please note down your details.",
                "calendar_event_id": calendar_result.get('event_id'),
                "email_error": email_result.get('error'),
                "appointment_details": {
                    "patient": patient_name,
                    "date": appointment_date,
                    "time": appointment_time,
                    "doctor": doctor_name,
                    "department": department
                }
            })
        else:
            error_msg = f"Both email and calendar failed. Email: {email_result.get('error')}. Calendar: {calendar_result.get('error')}"
            print(f"=== [ERROR] {error_msg} ===")
            await params.result_callback({
                "success": False,
                "error": error_msg,
                "message": "Sorry, I couldn't send the confirmation email or update the calendar. Please contact us directly."
            })

    except Exception as e:
        error_msg = f"Error processing appointment: {str(e)}"
        print(f"=== [ERROR] {error_msg} ===")
        logger.error(error_msg)
        await params.result_callback({
            "success": False,
            "error": error_msg,
            "message": "There was an error processing your appointment. Please contact us directly."
        })