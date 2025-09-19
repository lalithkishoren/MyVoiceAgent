#!/usr/bin/env python3

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from gmail_service import get_gmail_service
from calendar_service import get_calendar_service
from call_logger import get_call_logger, CallType, CustomerType, CallStatus
from language_support import get_language_manager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Define the check availability function schema
check_availability_function = FunctionSchema(
    name="check_appointment_availability",
    description="Check if a requested appointment time slot is available and suggest alternatives if not",
    properties={
        "appointment_date": {
            "type": "string",
            "description": "Date of the appointment (YYYY-MM-DD format, e.g., 2024-01-15)"
        },
        "appointment_time": {
            "type": "string",
            "description": "Time of the appointment (e.g., 10:00 AM)"
        },
        "duration_minutes": {
            "type": "integer",
            "description": "Duration of appointment in minutes (default: 30)"
        }
    },
    required=["appointment_date", "appointment_time"]
)

# Define the appointment booking function schema
book_appointment_function = FunctionSchema(
    name="book_appointment",
    description="Book an appointment after availability is confirmed - automatically sends email confirmation and adds to calendar",
    properties={
        "patient_name": {
            "type": "string",
            "description": "Full name of the patient (must be in English)"
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
            "description": "Date of the appointment (YYYY-MM-DD format, e.g., 2024-01-15)"
        },
        "appointment_time": {
            "type": "string",
            "description": "Time of the appointment (e.g., 10:00 AM)"
        },
        "doctor_name": {
            "type": "string",
            "description": "Name of the doctor assigned (must be in English)"
        },
        "department": {
            "type": "string",
            "description": "Hospital department (e.g., Cardiology, General Medicine)"
        },
        "customer_type": {
            "type": "string",
            "description": "Whether patient is new or existing customer",
            "enum": ["new", "existing"]
        },
        "language_used": {
            "type": "string",
            "description": "Language being used for conversation",
            "enum": ["english", "hindi", "telugu"]
        }
    },
    required=["patient_name", "email", "appointment_date", "appointment_time", "doctor_name", "department"]
)

# Define the appointment cancellation function schema
cancel_appointment_function = FunctionSchema(
    name="cancel_appointment",
    description="Cancel an existing appointment with verification of patient details",
    properties={
        "patient_name": {
            "type": "string",
            "description": "Full name of the patient (must match exactly)"
        },
        "patient_email": {
            "type": "string",
            "description": "Patient's email address for verification"
        },
        "patient_phone": {
            "type": "string",
            "description": "Patient's phone number for verification"
        },
        "appointment_date": {
            "type": "string",
            "description": "Date of the appointment to cancel (YYYY-MM-DD format)"
        },
        "appointment_time": {
            "type": "string",
            "description": "Time of the appointment to cancel (e.g., 10:00 AM)"
        },
        "doctor_name": {
            "type": "string",
            "description": "Name of the doctor for verification"
        },
        "language_used": {
            "type": "string",
            "description": "Language being used for conversation",
            "enum": ["english", "hindi", "telugu"]
        }
    },
    required=["patient_name", "appointment_date", "appointment_time", "doctor_name"]
)

# Define the call logging function schema
log_call_info_function = FunctionSchema(
    name="log_call_information",
    description="Log comprehensive call information including customer details and call summary",
    properties={
        "customer_name": {
            "type": "string",
            "description": "Customer's full name (English only)"
        },
        "customer_phone": {
            "type": "string",
            "description": "Customer's phone number"
        },
        "customer_email": {
            "type": "string",
            "description": "Customer's email address"
        },
        "call_type": {
            "type": "string",
            "description": "Type of call",
            "enum": ["appointment_booking", "appointment_cancellation", "general_enquiry", "department_enquiry", "doctor_enquiry", "billing_enquiry", "emergency", "other"]
        },
        "customer_type": {
            "type": "string",
            "description": "Whether customer is new or existing",
            "enum": ["new", "existing", "unknown"]
        },
        "department_enquired": {
            "type": "string",
            "description": "Department patient asked about"
        },
        "doctor_enquired": {
            "type": "string",
            "description": "Doctor patient asked about"
        },
        "call_summary": {
            "type": "string",
            "description": "Brief summary of the call conversation"
        },
        "resolution_status": {
            "type": "string",
            "description": "How the call was resolved",
            "enum": ["resolved", "partially_resolved", "unresolved", "escalated", "follow_up_required"]
        },
        "language_used": {
            "type": "string",
            "description": "Language used during the call",
            "enum": ["english", "hindi", "telugu"]
        }
    },
    required=["customer_name", "call_type", "call_summary"]
)

# Customer detection function schema (moved here for proper order)
detect_customer_function = FunctionSchema(
    name="detect_customer_type",
    description="Check customer type and retrieve existing information based on phone number",
    properties={
        "phone_number": {
            "type": "string",
            "description": "Patient's phone number to check in database"
        },
        "patient_name": {
            "type": "string",
            "description": "Patient's name for verification"
        }
    },
    required=["phone_number", "patient_name"]
)

# Create tools schema with all appointment functions
enhanced_appointment_tools = ToolsSchema(standard_tools=[
    detect_customer_function,
    check_availability_function,
    book_appointment_function,
    cancel_appointment_function,
    log_call_info_function
])

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

async def handle_check_appointment_availability(params: FunctionCallParams):
    """Handle checking appointment availability and suggest alternatives"""
    try:
        function_args = params.arguments
        appointment_date = function_args.get("appointment_date")
        appointment_time = function_args.get("appointment_time")
        duration_minutes = function_args.get("duration_minutes", 30)

        print(f"=== FUNCTION CALL: check_appointment_availability ===")
        print(f"Date: {appointment_date}")
        print(f"Time: {appointment_time}")
        print(f"Duration: {duration_minutes} minutes")

        # Check availability using calendar service
        calendar_service = get_calendar_service()
        availability_result = calendar_service.check_availability(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=duration_minutes
        )

        if availability_result.get('success'):
            if availability_result.get('available'):
                print(f"=== [AVAILABLE] Time slot is free ===")
                await params.result_callback({
                    "success": True,
                    "available": True,
                    "message": availability_result.get('message'),
                    "requested_slot": availability_result.get('requested_slot')
                })
            else:
                print(f"=== [UNAVAILABLE] Time slot is busy, suggesting alternatives ===")
                lang_manager = get_language_manager()
                alternatives_text = lang_manager.format_alternative_slots(
                    availability_result.get('alternatives', [])
                )
                await params.result_callback({
                    "success": True,
                    "available": False,
                    "message": availability_result.get('message'),
                    "conflicts": availability_result.get('conflicts', []),
                    "alternatives": availability_result.get('alternatives', []),
                    "alternatives_formatted": alternatives_text
                })
        else:
            error_msg = availability_result.get('error', 'Failed to check availability')
            print(f"=== [ERROR] {error_msg} ===")
            await params.result_callback({
                "success": False,
                "error": error_msg,
                "message": "I couldn't check the availability right now. Please try again."
            })

    except Exception as e:
        error_msg = f"Error checking availability: {str(e)}"
        print(f"=== [ERROR] {error_msg} ===")
        logger.error(error_msg)
        await params.result_callback({
            "success": False,
            "error": error_msg,
            "message": "There was an error checking availability. Please try again."
        })

async def handle_book_appointment(params: FunctionCallParams):
    """Handle booking appointment with email, calendar, and call logging"""
    try:
        function_args = params.arguments

        patient_name = function_args.get("patient_name")
        email = function_args.get("email")
        phone = function_args.get("phone", "Not provided")
        appointment_date = function_args.get("appointment_date")
        appointment_time = function_args.get("appointment_time")
        doctor_name = function_args.get("doctor_name")
        department = function_args.get("department")
        customer_type = function_args.get("customer_type", "unknown")
        language_used = function_args.get("language_used", "english")

        print(f"=== FUNCTION CALL: book_appointment ===")
        print(f"Patient: {patient_name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print(f"Date: {appointment_date}")
        print(f"Time: {appointment_time}")
        print(f"Doctor: {doctor_name}")
        print(f"Department: {department}")
        print(f"Customer Type: {customer_type}")
        print(f"Language: {language_used}")

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

        # 1. Double-check availability before booking
        calendar_service = get_calendar_service()
        availability_check = calendar_service.check_availability(
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )

        if not availability_check.get('available', True):  # Default to True if check fails
            lang_manager = get_language_manager()
            alternatives_text = lang_manager.format_alternative_slots(
                availability_check.get('alternatives', [])
            )
            await params.result_callback({
                "success": False,
                "available": False,
                "message": "Sorry, that time slot is no longer available. Please choose from these alternatives.",
                "alternatives": availability_check.get('alternatives', []),
                "alternatives_formatted": alternatives_text
            })
            return

        # 2. Create email content
        subject, body = create_appointment_email_html(
            patient_name, email, phone, appointment_date,
            appointment_time, doctor_name, department
        )

        # 3. Send email
        gmail_service = get_gmail_service()
        email_result = gmail_service.send_simple_email(
            to=email,
            subject=subject,
            body=body,
            is_html=True
        )

        # 4. Add to calendar
        calendar_result = calendar_service.create_appointment_event(
            patient_name=patient_name,
            patient_email=email,
            patient_phone=phone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            doctor_name=doctor_name,
            department=department
        )

        # 5. Log the call
        call_logger = get_call_logger()
        call_data = {
            "call_type": CallType.APPOINTMENT_BOOKING.value,
            "customer_name": patient_name,
            "caller_phone": phone,
            "customer_email": email,
            "customer_type": customer_type,
            "department_enquired": department,
            "doctor_enquired": doctor_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "language_used": language_used,
            "call_summary": f"Appointment booking for {patient_name} with {doctor_name} on {appointment_date} at {appointment_time}",
            "resolution_status": CallStatus.RESOLVED.value if email_result.get('success') and calendar_result.get('success') else CallStatus.PARTIALLY_RESOLVED.value,
            "agent_notes": f"Email: {'sent' if email_result.get('success') else 'failed'}, Calendar: {'added' if calendar_result.get('success') else 'failed'}"
        }
        call_logger.log_call(call_data)

        # 6. Evaluate results and respond
        email_success = email_result.get('success', False)
        calendar_success = calendar_result.get('success', False)

        if email_success and calendar_success:
            lang_manager = get_language_manager()
            confirmation_text = lang_manager.format_appointment_confirmation(
                patient_name, doctor_name, appointment_date, appointment_time, language_used
            )

            success_msg = f"Appointment confirmed! Email sent to {email} and added to hospital calendar."
            print(f"=== [SUCCESS] Email + Calendar: {success_msg} ===")
            await params.result_callback({
                "success": True,
                "message": success_msg,
                "confirmation_text": confirmation_text,
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
        else:
            # Handle partial success or failure
            error_parts = []
            if not email_success:
                error_parts.append(f"Email: {email_result.get('error')}")
            if not calendar_success:
                error_parts.append(f"Calendar: {calendar_result.get('error')}")

            error_msg = "; ".join(error_parts)
            print(f"=== [PARTIAL/ERROR] {error_msg} ===")
            await params.result_callback({
                "success": email_success or calendar_success,
                "message": "Appointment partially processed. Please contact us to confirm all details.",
                "error": error_msg,
                "email_success": email_success,
                "calendar_success": calendar_success
            })

    except Exception as e:
        error_msg = f"Error booking appointment: {str(e)}"
        print(f"=== [ERROR] {error_msg} ===")
        logger.error(error_msg)
        await params.result_callback({
            "success": False,
            "error": error_msg,
            "message": "There was an error booking your appointment. Please contact us directly."
        })

async def handle_cancel_appointment(params: FunctionCallParams):
    """Handle appointment cancellation with verification"""
    try:
        function_args = params.arguments

        patient_name = function_args.get("patient_name")
        patient_email = function_args.get("patient_email", "")
        patient_phone = function_args.get("patient_phone", "")
        appointment_date = function_args.get("appointment_date")
        appointment_time = function_args.get("appointment_time")
        doctor_name = function_args.get("doctor_name")
        language_used = function_args.get("language_used", "english")

        print(f"=== FUNCTION CALL: cancel_appointment ===")
        print(f"Patient: {patient_name}")
        print(f"Email: {patient_email}")
        print(f"Phone: {patient_phone}")
        print(f"Date: {appointment_date}")
        print(f"Time: {appointment_time}")
        print(f"Doctor: {doctor_name}")
        print(f"Language: {language_used}")

        # Validate required fields
        if not all([patient_name, appointment_date, appointment_time, doctor_name]):
            error_msg = "Missing required cancellation details"
            print(f"=== [ERROR] {error_msg} ===")
            await params.result_callback({
                "success": False,
                "error": error_msg,
                "message": "Please provide patient name, doctor name, appointment date and time for cancellation."
            })
            return

        # Cancel appointment using calendar service
        calendar_service = get_calendar_service()
        cancellation_result = calendar_service.cancel_appointment(
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone=patient_phone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            doctor_name=doctor_name
        )

        # Log the cancellation call
        call_logger = get_call_logger()
        call_data = {
            "call_type": CallType.APPOINTMENT_CANCELLATION.value,
            "customer_name": patient_name,
            "caller_phone": patient_phone,
            "customer_email": patient_email,
            "doctor_enquired": doctor_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "language_used": language_used,
            "call_summary": f"Appointment cancellation request for {patient_name} with {doctor_name} on {appointment_date} at {appointment_time}",
            "resolution_status": CallStatus.RESOLVED.value if cancellation_result.get('success') else CallStatus.UNRESOLVED.value,
            "agent_notes": f"Cancellation: {'successful' if cancellation_result.get('success') else 'failed - ' + cancellation_result.get('error', 'unknown error')}"
        }
        call_logger.log_call(call_data)

        if cancellation_result.get('success'):
            success_msg = cancellation_result.get('message')
            print(f"=== [SUCCESS] {success_msg} ===")

            # Send cancellation email if email is provided
            if patient_email:
                gmail_service = get_gmail_service()
                cancellation_email_result = gmail_service.send_simple_email(
                    to=patient_email,
                    subject=f"Appointment Cancelled - Renova Hospitals - {appointment_date}",
                    body=f"""Dear {patient_name},

Your appointment has been successfully cancelled:

Doctor: {doctor_name}
Date: {appointment_date}
Time: {appointment_time}

If you need to reschedule, please call us.

Thank you,
Renova Hospitals"""
                )

            await params.result_callback({
                "success": True,
                "message": success_msg,
                "cancelled_appointment": cancellation_result.get('cancelled_appointment'),
                "email_sent": bool(patient_email)
            })
        else:
            error_msg = cancellation_result.get('error')
            print(f"=== [ERROR] {error_msg} ===")
            await params.result_callback({
                "success": False,
                "error": error_msg,
                "message": "Could not cancel the appointment. Please verify the details and try again.",
                "provided_details": cancellation_result.get('provided_details')
            })

    except Exception as e:
        error_msg = f"Error cancelling appointment: {str(e)}"
        print(f"=== [ERROR] {error_msg} ===")
        logger.error(error_msg)
        await params.result_callback({
            "success": False,
            "error": error_msg,
            "message": "There was an error cancelling your appointment. Please contact us directly."
        })

async def handle_log_call_information(params: FunctionCallParams):
    """Handle logging comprehensive call information"""
    try:
        function_args = params.arguments

        customer_name = function_args.get("customer_name")
        customer_phone = function_args.get("customer_phone", "")
        customer_email = function_args.get("customer_email", "")
        call_type = function_args.get("call_type")
        customer_type = function_args.get("customer_type", "unknown")
        department_enquired = function_args.get("department_enquired", "")
        doctor_enquired = function_args.get("doctor_enquired", "")
        call_summary = function_args.get("call_summary")
        resolution_status = function_args.get("resolution_status", "resolved")
        language_used = function_args.get("language_used", "english")

        print(f"=== FUNCTION CALL: log_call_information ===")
        print(f"Customer: {customer_name}")
        print(f"Phone: {customer_phone}")
        print(f"Type: {call_type}")
        print(f"Summary: {call_summary}")
        print(f"Language: {language_used}")

        # Log the call
        call_logger = get_call_logger()
        call_data = {
            "call_type": call_type,
            "customer_name": customer_name,
            "caller_phone": customer_phone,
            "customer_email": customer_email,
            "customer_type": customer_type,
            "department_enquired": department_enquired,
            "doctor_enquired": doctor_enquired,
            "call_summary": call_summary,
            "language_used": language_used,
            "resolution_status": resolution_status,
            "agent_notes": "Call logged via voice agent function calling"
        }

        call_id = call_logger.log_call(call_data)

        print(f"=== [SUCCESS] Call logged with ID: {call_id} ===")
        await params.result_callback({
            "success": True,
            "message": "Call information logged successfully",
            "call_id": call_id
        })

    except Exception as e:
        error_msg = f"Error logging call: {str(e)}"
        print(f"=== [ERROR] {error_msg} ===")
        logger.error(error_msg)
        await params.result_callback({
            "success": False,
            "error": error_msg,
            "message": "Could not log call information"
        })

async def handle_detect_customer_type(params: FunctionCallParams):
    """Handle customer detection and information retrieval"""
    try:
        function_args = params.arguments
        phone_number = function_args.get("phone_number")
        patient_name = function_args.get("patient_name")

        print(f"=== FUNCTION CALL: detect_customer_type ===")
        print(f"Phone: {phone_number}")
        print(f"Name: {patient_name}")

        # Get Google Sheets service - access global variable from main server
        import pipecat_server
        sheets_service = getattr(pipecat_server, 'global_sheets_service', None)

        customer_type = "new"
        customer_info = None

        if sheets_service:
            try:
                # Check Google Sheets for existing customer
                existing_patient = sheets_service.get_patient_by_phone(phone_number)

                if existing_patient:
                    customer_type = "returning"
                    customer_info = {
                        "name": existing_patient.name,
                        "email": existing_patient.email,
                        "phone": existing_patient.phone,
                        "preferred_doctor": existing_patient.preferred_doctor,
                        "department": existing_patient.department,
                        "language": existing_patient.language,
                        "last_visit": existing_patient.last_visit
                    }
                    print(f"=== [RETURNING CUSTOMER] Found: {existing_patient.name} ===")
                else:
                    print(f"=== [NEW CUSTOMER] Not found in database ===")

            except Exception as e:
                print(f"=== [ERROR] Database check failed: {e} ===")
                customer_type = "new"

        # Prepare response based on customer type
        if customer_type == "returning" and customer_info:
            message = f"Welcome back {customer_info['name']}! I found your information in our system."
            if customer_info.get('preferred_doctor'):
                message += f" Would you like to book with Dr. {customer_info['preferred_doctor']} again?"

            await params.result_callback({
                "success": True,
                "customer_type": "returning",
                "customer_info": customer_info,
                "message": message,
                "skip_email_collection": True,
                "suggested_doctor": customer_info.get('preferred_doctor'),
                "suggested_department": customer_info.get('department')
            })
        else:
            await params.result_callback({
                "success": True,
                "customer_type": "new",
                "customer_info": None,
                "message": f"Thank you {patient_name}. I'll help you book your first appointment with us.",
                "skip_email_collection": False
            })

    except Exception as e:
        error_msg = f"Error detecting customer type: {str(e)}"
        print(f"=== [ERROR] {error_msg} ===")
        logger.error(error_msg)
        await params.result_callback({
            "success": False,
            "error": error_msg,
            "message": "I'll help you as a new patient."
        })

# Function registry for easy registration with LLM
ENHANCED_FUNCTION_REGISTRY = {
    "detect_customer_type": handle_detect_customer_type,
    "check_appointment_availability": handle_check_appointment_availability,
    "book_appointment": handle_book_appointment,
    "cancel_appointment": handle_cancel_appointment,
    "log_call_information": handle_log_call_information
}