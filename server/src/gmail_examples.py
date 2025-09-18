#!/usr/bin/env python3
"""
Gmail Integration Examples
Practical examples for using Gmail functionality in your voice agent
"""

import asyncio
import json
from datetime import datetime
from gmail_service import get_gmail_service, EmailMessage
from voice_email_handler import get_voice_email_handler

def example_1_simple_email():
    """Example 1: Send a simple text email"""
    print("📧 Example 1: Simple Email")

    gmail_service = get_gmail_service()

    result = gmail_service.send_simple_email(
        to="patient@example.com",
        subject="Appointment Confirmation - Renova Hospitals",
        body="Dear Patient,\n\nYour appointment has been confirmed for:\n\nDate: Tomorrow, 2:00 PM\nDoctor: Dr. Smith\nDepartment: Cardiology\n\nPlease arrive 15 minutes early.\n\nBest regards,\nRenova Hospitals"
    )

    print(f"Result: {result}")

def example_2_html_email():
    """Example 2: Send a formatted HTML email"""
    print("📧 Example 2: HTML Email")

    gmail_service = get_gmail_service()

    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px;">
            <h2 style="color: #2c5aa0;">🏥 Renova Hospitals</h2>
            <h3>Test Results Available</h3>

            <p>Dear Patient,</p>

            <p>Your recent lab results are now available for review.</p>

            <div style="background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2c5aa0;">
                <strong>Next Steps:</strong>
                <ul>
                    <li>Review results in patient portal</li>
                    <li>Schedule follow-up if needed</li>
                    <li>Contact us with questions</li>
                </ul>
            </div>

            <p style="color: #666;">
                This email was sent by your Renova Hospitals Voice Assistant.
            </p>
        </div>
    </body>
    </html>
    """

    result = gmail_service.send_simple_email(
        to="patient@example.com",
        subject="📋 Test Results - Renova Hospitals",
        body=html_content,
        is_html=True
    )

    print(f"Result: {result}")

def example_3_voice_commands():
    """Example 3: Process various voice commands"""
    print("🎤 Example 3: Voice Commands")

    voice_handler = get_voice_email_handler()

    voice_commands = [
        "Send an email to doctor@hospital.com about my appointment saying I need to reschedule",
        "Email the billing department regarding my invoice",
        "Write an email to support@hospital.com",
        "Can you send an appointment confirmation to patient@email.com?"
    ]

    for i, command in enumerate(voice_commands, 1):
        print(f"\n🗣️  Command {i}: '{command}'")

        result = voice_handler.process_voice_command(command, f"session-{i}")

        print(f"   Action: {result['action']}")
        print(f"   Message: {result.get('message', 'None')}")
        print(f"   Needs Response: {result['requires_response']}")

def example_4_notification_emails():
    """Example 4: Send automated notification emails"""
    print("📬 Example 4: Notification Emails")

    voice_handler = get_voice_email_handler()

    # Call summary notification
    call_summary = {
        "caller": "+1-555-0123",
        "caller_name": "John Smith",
        "duration": "7 minutes",
        "summary": "Patient called regarding medication side effects. Discussed current symptoms and scheduled follow-up appointment for next week.",
        "department": "Internal Medicine",
        "action_required": "Schedule follow-up appointment"
    }

    result1 = voice_handler.send_notification_email(
        to="doctor@hospital.com",
        event_type="call_summary",
        details=call_summary
    )
    print(f"Call summary result: {result1}")

    # Appointment request notification
    appointment_request = {
        "patient_name": "Sarah Johnson",
        "phone": "+1-555-0456",
        "email": "sarah.j@email.com",
        "preferred_date": "Next Monday",
        "preferred_time": "Morning",
        "reason": "Annual checkup",
        "insurance": "Blue Cross Blue Shield",
        "new_patient": False
    }

    result2 = voice_handler.send_notification_email(
        to="reception@hospital.com",
        event_type="appointment_request",
        details=appointment_request
    )
    print(f"Appointment request result: {result2}")

def example_5_multi_step_email():
    """Example 5: Multi-step email composition"""
    print("👥 Example 5: Multi-step Email Composition")

    voice_handler = get_voice_email_handler()
    session_id = "multi-step-demo"

    steps = [
        "I want to send an email",
        "Send it to nurse@hospital.com",
        "Subject should be medication inquiry",
        "The message is: I have questions about my new prescription. What are the potential side effects and when should I take it?"
    ]

    for i, step in enumerate(steps, 1):
        print(f"\n📝 Step {i}: '{step}'")

        result = voice_handler.process_voice_command(step, session_id)

        print(f"   Action: {result['action']}")
        print(f"   Response: {result.get('message', 'None')}")

        if result.get('current_info'):
            print(f"   Current Info: {result['current_info']}")

def example_6_context_management():
    """Example 6: Context management and session cleanup"""
    print("🧠 Example 6: Context Management")

    voice_handler = get_voice_email_handler()

    # Create some contexts
    sessions = ["session-1", "session-2", "session-3"]

    for session in sessions:
        voice_handler.process_voice_command(
            f"Send email to user{session[-1]}@example.com",
            session
        )

    print(f"Active contexts: {len(voice_handler.email_context)}")
    print(f"Context sessions: {list(voice_handler.email_context.keys())}")

    # Cleanup old contexts
    voice_handler.cleanup_old_contexts(max_age_minutes=0)  # Cleanup immediately

    print(f"Contexts after cleanup: {len(voice_handler.email_context)}")

def example_7_email_templates():
    """Example 7: Using email templates for common scenarios"""
    print("📋 Example 7: Email Templates")

    gmail_service = get_gmail_service()

    # Template 1: Appointment confirmation
    def send_appointment_confirmation(patient_email, patient_name, appointment_date, doctor_name, department):
        template = f"""
        <html>
        <body>
            <h2>🏥 Appointment Confirmed - Renova Hospitals</h2>

            <p>Dear {patient_name},</p>

            <p>Your appointment has been successfully scheduled:</p>

            <div style="background-color: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <strong>📅 Date & Time:</strong> {appointment_date}<br>
                <strong>👨‍⚕️ Doctor:</strong> {doctor_name}<br>
                <strong>🏥 Department:</strong> {department}<br>
            </div>

            <p><strong>Important:</strong></p>
            <ul>
                <li>Please arrive 15 minutes early</li>
                <li>Bring your insurance card and ID</li>
                <li>Bring a list of current medications</li>
            </ul>

            <p>If you need to reschedule, please call us at least 24 hours in advance.</p>

            <p>Best regards,<br>Renova Hospitals Team</p>
        </body>
        </html>
        """

        return gmail_service.send_simple_email(
            to=patient_email,
            subject=f"Appointment Confirmed - {appointment_date}",
            body=template,
            is_html=True
        )

    # Template 2: Test results notification
    def send_test_results_notification(patient_email, patient_name, test_type):
        template = f"""
        <html>
        <body>
            <h2>📋 Test Results Available - Renova Hospitals</h2>

            <p>Dear {patient_name},</p>

            <p>Your <strong>{test_type}</strong> results are now available for review.</p>

            <p>You can:</p>
            <ul>
                <li>View results in our patient portal</li>
                <li>Call us to discuss results with your doctor</li>
                <li>Schedule a follow-up appointment if recommended</li>
            </ul>

            <p>If you have any questions, please don't hesitate to contact us.</p>

            <p>Best regards,<br>Renova Hospitals Team</p>
        </body>
        </html>
        """

        return gmail_service.send_simple_email(
            to=patient_email,
            subject=f"{test_type} Results Available",
            body=template,
            is_html=True
        )

    # Example usage
    result1 = send_appointment_confirmation(
        patient_email="patient@example.com",
        patient_name="John Doe",
        appointment_date="Tomorrow, 2:00 PM",
        doctor_name="Dr. Smith",
        department="Cardiology"
    )
    print(f"Appointment confirmation: {result1}")

    result2 = send_test_results_notification(
        patient_email="patient@example.com",
        patient_name="Jane Doe",
        test_type="Blood Test"
    )
    print(f"Test results notification: {result2}")

def run_all_examples():
    """Run all examples (except actual email sending)"""
    examples = [
        example_3_voice_commands,
        example_5_multi_step_email,
        example_6_context_management,
    ]

    print("🚀 Running Gmail Integration Examples")
    print("=" * 50)

    for example in examples:
        try:
            print(f"\n{'='*50}")
            example()
        except Exception as e:
            print(f"❌ Error in example: {str(e)}")

    print(f"\n{'='*50}")
    print("✅ All examples completed!")
    print("\nNote: Email sending examples (1, 2, 4, 7) require manual execution")
    print("to avoid sending test emails automatically.")

if __name__ == "__main__":
    print("Gmail Integration Examples")
    print("=" * 30)
    print("Choose an example to run:")
    print("1. Simple Email")
    print("2. HTML Email")
    print("3. Voice Commands")
    print("4. Notification Emails")
    print("5. Multi-step Email")
    print("6. Context Management")
    print("7. Email Templates")
    print("8. Run All (non-sending examples)")
    print("0. Exit")

    choice = input("\nEnter your choice (0-8): ").strip()

    examples_map = {
        "1": example_1_simple_email,
        "2": example_2_html_email,
        "3": example_3_voice_commands,
        "4": example_4_notification_emails,
        "5": example_5_multi_step_email,
        "6": example_6_context_management,
        "7": example_7_email_templates,
        "8": run_all_examples,
    }

    if choice in examples_map:
        try:
            examples_map[choice]()
        except Exception as e:
            print(f"❌ Error running example: {str(e)}")
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice. Please run the script again.")