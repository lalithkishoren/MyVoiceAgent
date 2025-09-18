#!/usr/bin/env python3
"""
Comprehensive test suite for Gmail integration
Run this script to test all Gmail functionality
"""

import asyncio
import json
import logging
from typing import Dict, Any
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmail_service import get_gmail_service, EmailMessage
from voice_email_handler import get_voice_email_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gmail_authentication():
    """Test Gmail service authentication and initialization"""
    print("\n=== Testing Gmail Authentication ===")
    try:
        gmail_service = get_gmail_service()
        profile = gmail_service.get_user_profile()

        if profile['success']:
            print(f"✅ Authentication successful!")
            print(f"   Email: {profile['email']}")
            print(f"   Total Messages: {profile['messages_total']}")
            print(f"   Total Threads: {profile['threads_total']}")
            return True
        else:
            print(f"❌ Authentication failed: {profile['error']}")
            return False

    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False

def test_simple_email_send():
    """Test sending a simple email"""
    print("\n=== Testing Simple Email Send ===")

    # Use your own email for testing
    test_email = input("Enter your email address for testing (or press Enter to skip): ").strip()
    if not test_email:
        print("⏭️  Skipping email send test")
        return True

    try:
        gmail_service = get_gmail_service()

        result = gmail_service.send_simple_email(
            to=test_email,
            subject="Test Email from Voice Agent",
            body="Hello! This is a test email from your Renova Hospitals Voice Agent. If you received this, the Gmail integration is working correctly!",
            is_html=False
        )

        if result['success']:
            print(f"✅ Email sent successfully!")
            print(f"   Message ID: {result['message_id']}")
            print(f"   Recipient: {result['recipient']}")
            return True
        else:
            print(f"❌ Email sending failed: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ Email sending error: {str(e)}")
        return False

def test_html_email_send():
    """Test sending an HTML email"""
    print("\n=== Testing HTML Email Send ===")

    test_email = input("Enter your email address for HTML email test (or press Enter to skip): ").strip()
    if not test_email:
        print("⏭️  Skipping HTML email test")
        return True

    try:
        gmail_service = get_gmail_service()

        html_body = """
        <html>
        <body>
            <h2 style="color: #2c5aa0;">Renova Hospitals Voice Agent</h2>
            <p>Dear Patient,</p>
            <p>This is a <strong>test HTML email</strong> from your voice agent system.</p>
            <ul>
                <li>✅ Authentication working</li>
                <li>✅ Gmail API integration active</li>
                <li>✅ HTML formatting supported</li>
            </ul>
            <p>Best regards,<br>
            <em>Archana - Voice Assistant</em></p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                Generated automatically by Renova Hospitals Voice Agent System
            </p>
        </body>
        </html>
        """

        result = gmail_service.send_simple_email(
            to=test_email,
            subject="HTML Test - Voice Agent System",
            body=html_body,
            is_html=True
        )

        if result['success']:
            print(f"✅ HTML email sent successfully!")
            print(f"   Message ID: {result['message_id']}")
            return True
        else:
            print(f"❌ HTML email sending failed: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ HTML email sending error: {str(e)}")
        return False

def test_voice_email_extraction():
    """Test voice command email extraction"""
    print("\n=== Testing Voice Email Extraction ===")

    test_cases = [
        "Send an email to doctor@hospital.com about appointment rescheduling saying I need to change my appointment time",
        "Email john@example.com regarding test results",
        "Write an email to nurse@clinic.com",
        "Send email to admin@hospital.com subject urgent matter message please call me back",
        "Can you email the doctor about my prescription?",
        "I want to send an email",
        "Email someone about something"
    ]

    try:
        voice_handler = get_voice_email_handler()

        for i, test_text in enumerate(test_cases, 1):
            print(f"\n🎤 Test Case {i}: '{test_text}'")

            components = voice_handler.extract_email_components(test_text)

            print(f"   Email Intent: {'✅' if components['has_email_intent'] else '❌'}")
            print(f"   Recipient: {components['recipient'] or 'Not found'}")
            print(f"   Subject: {components['subject'] or 'Not found'}")
            print(f"   Body: {components['body'] or 'Not found'}")
            print(f"   Emails Found: {components['emails_found']}")

        return True

    except Exception as e:
        print(f"❌ Voice extraction error: {str(e)}")
        return False

def test_voice_email_processing():
    """Test complete voice email processing workflow"""
    print("\n=== Testing Voice Email Processing ===")

    test_scenarios = [
        {
            "description": "Complete email command",
            "text": "Send an email to test@example.com subject Test Message body Hello this is a test",
            "session_id": "test-session-1"
        },
        {
            "description": "Partial email command - missing body",
            "text": "Send an email to support@hospital.com about appointment scheduling",
            "session_id": "test-session-2"
        },
        {
            "description": "Email intent without details",
            "text": "I want to send an email",
            "session_id": "test-session-3"
        },
        {
            "description": "Non-email command",
            "text": "What are your opening hours?",
            "session_id": "test-session-4"
        }
    ]

    try:
        voice_handler = get_voice_email_handler()

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📧 Scenario {i}: {scenario['description']}")
            print(f"   Input: '{scenario['text']}'")

            result = voice_handler.process_voice_command(
                scenario['text'],
                scenario['session_id']
            )

            print(f"   Action: {result['action']}")
            print(f"   Message: {result.get('message', 'None')}")
            print(f"   Requires Response: {result['requires_response']}")
            if result.get('missing_info'):
                print(f"   Missing Info: {result['missing_info']}")

        return True

    except Exception as e:
        print(f"❌ Voice processing error: {str(e)}")
        return False

def test_notification_email():
    """Test notification email functionality"""
    print("\n=== Testing Notification Email ===")

    test_email = input("Enter your email for notification test (or press Enter to skip): ").strip()
    if not test_email:
        print("⏭️  Skipping notification email test")
        return True

    try:
        voice_handler = get_voice_email_handler()

        # Test call summary notification
        call_details = {
            "caller": "+1-555-0123",
            "duration": "5 minutes 30 seconds",
            "summary": "Patient called to inquire about test results and reschedule appointment for next week.",
            "timestamp": "2024-01-15 14:30:00"
        }

        result = voice_handler.send_notification_email(
            to=test_email,
            event_type="call_summary",
            details=call_details
        )

        if result['success']:
            print(f"✅ Call summary notification sent!")
            print(f"   Message ID: {result.get('message_id', 'Unknown')}")
        else:
            print(f"❌ Notification failed: {result['error']}")
            return False

        # Test appointment request notification
        appointment_details = {
            "patient_name": "John Doe",
            "phone": "+1-555-0456",
            "preferred_date": "Next Monday",
            "reason": "Cardiology consultation",
            "notes": "Patient prefers morning appointments"
        }

        result = voice_handler.send_notification_email(
            to=test_email,
            event_type="appointment_request",
            details=appointment_details
        )

        if result['success']:
            print(f"✅ Appointment request notification sent!")
        else:
            print(f"❌ Appointment notification failed: {result['error']}")
            return False

        return True

    except Exception as e:
        print(f"❌ Notification email error: {str(e)}")
        return False

def test_context_management():
    """Test email context management across conversation turns"""
    print("\n=== Testing Context Management ===")

    try:
        voice_handler = get_voice_email_handler()
        session_id = "context-test-session"

        # First interaction - partial email
        print("\n🎭 Turn 1: Initial email request")
        result1 = voice_handler.process_voice_command(
            "Send an email to doctor@example.com",
            session_id
        )
        print(f"   Action: {result1['action']}")
        print(f"   Message: {result1.get('message', 'None')}")

        # Second interaction - provide subject
        print("\n🎭 Turn 2: Adding subject")
        result2 = voice_handler.process_voice_command(
            "Subject is appointment follow-up",
            session_id
        )
        print(f"   Action: {result2['action']}")
        print(f"   Message: {result2.get('message', 'None')}")

        # Third interaction - provide body
        print("\n🎭 Turn 3: Adding message body")
        result3 = voice_handler.process_voice_command(
            "Message is thank you for the consultation yesterday, I wanted to follow up on the treatment plan",
            session_id
        )
        print(f"   Action: {result3['action']}")
        print(f"   Message: {result3.get('message', 'None')}")

        # Check stored context
        if session_id in voice_handler.email_context:
            context = voice_handler.email_context[session_id]
            print(f"\n📝 Stored Context:")
            print(f"   Recipient: {context.get('recipient', 'None')}")
            print(f"   Subject: {context.get('subject', 'None')}")
            print(f"   Body: {context.get('body', 'None')}")

        # Cleanup context
        voice_handler.cleanup_old_contexts(0)  # Cleanup immediately for test

        return True

    except Exception as e:
        print(f"❌ Context management error: {str(e)}")
        return False

def run_comprehensive_tests():
    """Run all tests in sequence"""
    print("🚀 Starting Comprehensive Gmail Integration Tests")
    print("=" * 60)

    test_results = []

    # Run all tests
    tests = [
        ("Gmail Authentication", test_gmail_authentication),
        ("Voice Email Extraction", test_voice_email_extraction),
        ("Voice Email Processing", test_voice_email_processing),
        ("Context Management", test_context_management),
        ("Simple Email Send", test_simple_email_send),
        ("HTML Email Send", test_html_email_send),
        ("Notification Email", test_notification_email),
    ]

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            test_results.append((test_name, False))

    # Print summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Gmail integration is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the configuration.")

    return passed == total

if __name__ == "__main__":
    print("Gmail Integration Test Suite")
    print("This will test all aspects of the Gmail integration.")
    print("Make sure you have completed the setup in GMAIL_SETUP.md")
    print()

    try:
        # Check if we have required files
        if not os.path.exists("client_secrets.json"):
            print("❌ client_secrets.json not found!")
            print("Please follow GMAIL_SETUP.md to download OAuth2 credentials.")
            sys.exit(1)

        # Run comprehensive tests
        success = run_comprehensive_tests()

        if success:
            print("\n🌟 Gmail integration is ready for use!")
        else:
            print("\n🔧 Please fix the failing tests before using Gmail integration.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)